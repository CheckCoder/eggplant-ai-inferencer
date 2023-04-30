sudo apt install docker.io

git clone https://github.com/CheckCoder/eggplant-ai-inferencer.git
cd eggplant-ai-inferencer

curl https://replicate.github.io/codespaces/scripts/install-cog.sh | bash
cog --version

cog run script/download-weights

# cog predict -i prompt="monkey scuba diving" -i width=512  -i height=512

# wget -O image.jpg http://n.sinaimg.cn/sinakd20200320ac/30/w1080h1350/20200320/0089-ireifzh0650938.jpg
# cog predict -i image=@image.jpg

cog login
cog push