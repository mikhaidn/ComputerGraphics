#version 300 es
precision highp float;
uniform vec4 color;
out vec4 fragColor;
in vec4 color2;
in vec4 normals2;
void main(){
    vec3 lightDir=normalize(vec3(1.,1.,1.));
    
    // Get normal from interpolated vertex normal
    vec3 normal=normalize(normals2.xyz);
    
    // Calculate diffuse lighting
    float diffuse=max(dot(normal,lightDir),0.);
    
    // Add ambient light to avoid completely dark areas
    float ambient=.2;
    
    // Final color combines ambient and diffuse lighting
    vec3 finalColor=color2.rgb*(ambient+diffuse);
    
    fragColor=vec4(finalColor,1.);
}