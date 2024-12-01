#version 300 es
layout(location = 0) in vec4 position;
layout(location = 3) in vec2 aTexCoord;
uniform mat4 m;
uniform mat4 v;
uniform mat4 p;

out vec4 vnormal;
out vec2 vTexCoord;

void main() {
  gl_Position = p * v * m * position;
  vTexCoord = aTexCoord;
}