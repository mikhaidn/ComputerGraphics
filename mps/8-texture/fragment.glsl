#version 300 es
precision highp float;
uniform vec4 color;
out vec4 fragColor;
in vec4 color2;
in vec4 vnormal;

uniform vec3 lightdir;
uniform vec3 lightcolor;
uniform vec3 halfway;

void main(){
    
    vec3 n=normalize(vnormal.xyz);
    float lambert=max(dot(n,lightdir),0.);
    float blinn=pow(max(dot(n,halfway),0.),150.);
    
    vec3 finalColor=color2.rgb*(lightcolor*lambert)+((lightcolor*blinn)*2.);
    
    fragColor=vec4(finalColor,1.);
    // fragColor=vnormal;
    
}