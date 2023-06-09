import os
import math
from typing import List

import torch
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionImg2ImgPipeline,
    PNDMScheduler,
    LMSDiscreteScheduler,
    DDIMScheduler,
    EulerDiscreteScheduler,
    EulerAncestralDiscreteScheduler,
    DPMSolverMultistepScheduler,
    UniPCMultistepScheduler,
)
from PIL import Image
from cog import BasePredictor, Input, Path

MODEL_ID = "sinkinai/meinapastel"
MODEL_CACHE = "diffusers-cache"

def resize_image(image, x, y):
    return image.resize((x, y), Image.ANTIALIAS)

def resize_image_to_size(image, to_size):
    width, height = image.size
    image_size = width * height
    if image_size <= to_size:
        return image

    # w / h = x / y
    # x * y = to_size
    # x * x = w / h * to_size
    x = round(math.sqrt(width / height * to_size))
    y = round(to_size / x)
    return resize_image(image, x, y)

class Predictor(BasePredictor):
    def setup(self):
        """Load the model into memory to make running multiple predictions efficient"""
        print("Loading pipeline...")
        self.txt2img_pipe = StableDiffusionPipeline.from_pretrained(
            MODEL_ID,
            cache_dir=MODEL_CACHE,
            local_files_only=True,
        ).to("cuda")
        self.img2img_pipe = StableDiffusionImg2ImgPipeline(
            vae=self.txt2img_pipe.vae,
            text_encoder=self.txt2img_pipe.text_encoder,
            tokenizer=self.txt2img_pipe.tokenizer,
            unet=self.txt2img_pipe.unet,
            scheduler=self.txt2img_pipe.scheduler,
            safety_checker=self.txt2img_pipe.safety_checker,
            feature_extractor=self.txt2img_pipe.feature_extractor,
        ).to("cuda")
        self.img2img_pipe.safety_checker = lambda images, clip_input: (images, False)

    @torch.inference_mode()
    def predict(
        self,
        prompt: str = Input(
            description="Input prompt",
            default="(Masterpiece), (Best Quality), (Ultra Detailed), (1 girl), smiling, cute, bangs:0.7, black hair, (beautiful and detailed face) , official art",
        ),
        negative_prompt: str = Input(
            description="Input negative prompt",
            default="(low quality: 1.3), (worst quality: 1.3), (zombie, sketch, interlocking, manga), boy, boobs, boobs, porn,text,No more than five fingers, bad anatomy, (((bad hands))), error, missing fingers",
        ),
        image: Path = Input(
            description="Inital image to generate variations of.",
        ),
        # width: int = Input(
        #     description="Width of output image. Maximum size is 1024x768 or 768x1024 because of memory limits",
        #     choices=[128, 256, 384, 448, 512, 576, 640, 704, 768, 832, 896, 960, 1024],
        #     default=512,
        # ),
        # height: int = Input(
        #     description="Height of output image. Maximum size is 1024x768 or 768x1024 because of memory limits",
        #     choices=[128, 256, 384, 448, 512, 576, 640, 704, 768, 832, 896, 960, 1024],
        #     default=512,
        # ),
        prompt_strength: float = Input(
            description="Prompt strength when providing the image. 1.0 corresponds to full destruction of information in init image",
            default=0.26,
        ),
        num_outputs: int = Input(
            description="Number of images to output. Higher number of outputs may OOM.",
            ge=1,
            le=8,
            default=1,
        ),
        num_inference_steps: int = Input(
            description="Number of denoising steps", ge=1, le=500, default=25
        ),
        guidance_scale: float = Input(
            description="Scale for classifier-free guidance", ge=1, le=20, default=7.0
        ),
        scheduler: str = Input(
            default="DPMSolverMultistep",
            choices=["DPMSolverMultistep", "UniPCMultistepScheduler", "DDIM", "K_EULER", "K_EULER_ANCESTRAL", "PNDM", "KLMS"],
            description="Choose a scheduler.",
        ),
        seed: int = Input(
            description="Random seed. Leave blank to randomize the seed", default=1185332774
        ),
        max_image_size: int = Input(
            description="Max image size, if it exceeds, it will compress", default=786432
        )
    ) -> List[Path]:
        """Run a single prediction on the model"""
        if seed is None:
            seed = int.from_bytes(os.urandom(2), "big")
        print(f"Using seed: {seed}")

        image = Image.open(image).convert("RGB")
        image = resize_image_to_size(image, max_image_size)

        pipe = self.img2img_pipe
        extra_kwargs = {
            "image": image,
            "strength": prompt_strength,
        }
        pipe.scheduler = make_scheduler(scheduler, pipe.scheduler.config)

        generator = torch.Generator("cuda").manual_seed(seed)
        output = pipe(
            prompt=[prompt] * num_outputs if prompt is not None else None,
            negative_prompt=[negative_prompt] * num_outputs if negative_prompt is not None else None,
            guidance_scale=guidance_scale,
            generator=generator,
            num_inference_steps=num_inference_steps,
            **extra_kwargs,
        )

        output_paths = []
        for i, sample in enumerate(output.images):
            output_path = f"/tmp/out-{i}.png"
            sample.save(output_path)
            output_paths.append(Path(output_path))

        return output_paths


def make_scheduler(name, config):
    return {
        "PNDM": PNDMScheduler.from_config(config),
        "KLMS": LMSDiscreteScheduler.from_config(config),
        "DDIM": DDIMScheduler.from_config(config),
        "K_EULER": EulerDiscreteScheduler.from_config(config),
        "K_EULER_ANCESTRAL": EulerAncestralDiscreteScheduler.from_config(config),
        "DPMSolverMultistep": DPMSolverMultistepScheduler.from_config(config),
        "UniPCMultistepScheduler": UniPCMultistepScheduler.from_config(config),
    }[name]
