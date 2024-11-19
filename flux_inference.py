import torch
from diffusers import FluxPipeline

pipe = FluxPipeline.from_pretrained("/ssd2/jinxiu/weights/FLUX.1-dev", torch_dtype=torch.bfloat16).to('cuda')
pipe.enable_model_cpu_offload() #save some VRAM by offloading the model to CPU. Remove this if you have enough GPU power

pipe.load_lora_weights(
    pretrained_model_name_or_path_or_dict="/ssd2/jinxiu/weights/FLUX.1-dev",
    weight_name="/ssd1/jinxiu/PhysVideoGen/In-Context-LoRA/360_flux1_lora_aitoolkit_000006000.safetensors"
)

prompt = "A cat holding a sign that says trump out,360, panorama, spherical panorama"

image = pipe(
    prompt,
    height=512,
    width=1024,
    guidance_scale=3.5,
    num_inference_steps=50,
    max_sequence_length=512,
    generator=torch.Generator("cuda").manual_seed(0)
).images[0]
image.save("flux-dev.png")







