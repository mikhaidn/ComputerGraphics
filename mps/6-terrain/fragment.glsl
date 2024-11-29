#version 300 es
precision highp float;
uniform vec4 color;
out vec4 fragColor;
in vec4 color2;
in vec4 vnormal;
uniform vec3 diffuse_tone;
void main(){
    vec3 lightDir=normalize(vec3(1.,1.,1.));
    
    vec3 normal=vnormal.xyz;
    
    // Calculate lambert diffusion
    float diffuse=max(dot(normal,lightDir),0.);
    
    float ambient=.2;
    
    // Add spe
    
    // Final color combines ambient and diffuse lighting
    vec3 finalColor=color2.rgb*(ambient+diffuse);
    
    fragColor=vec4(finalColor,1.);
    // fragColor=vnormal;
}