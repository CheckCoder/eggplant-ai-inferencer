# cog-stable-diffusion-img2img


[![Replicate](https://replicate.com/replicate/stable-diffusion-img2img/badge)](https://replicate.com/replicate/stable-diffusion-img2img) 

This is an implementation of the [Diffusers Stable Diffusion v2.1](https://huggingface.co/stabilityai/stable-diffusion-2-1) as a Cog model. [Cog packages machine learning models as standard containers.](https://github.com/replicate/cog)

First, download the pre-trained weights:

    cog run script/download-weights 

Then, you can run predictions:

    cog predict -i prompt="..." -i image=@... 


GPU: 计算型 gn6i / ecs.gn6i-c4g1.xlarge (4vCPU 15GiB)
硬盘: 100G
按流量计费：50Mbps
!Test