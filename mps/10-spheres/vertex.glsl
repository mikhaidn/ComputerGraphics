#version 300 es
layout(location = 0) in vec4 position;
layout(location = 2) in vec3 normal;
out vec3 vnormal;
uniform mat4 m;
uniform mat4 v;
uniform mat4 p;

void main() {
    gl_Position = p * v * m * position;
    vnormal = normal;
}