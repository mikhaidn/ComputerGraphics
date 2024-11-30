#version 300 es
layout(location=0)in vec4 position;
layout(location=1)in vec4 color;
layout(location=2)in vec4 normal;
out vec4 color2;
out vec4 vnormal;
uniform mat4 m;
uniform mat4 v;
uniform mat4 p;

uniform vec3 diffuse_tone;
void main(){
    gl_Position=p*v*m*position;
    color2=color;
    vnormal=normal;
}