#version 300 es
precision highp float; // a precision statmeent is required for fragment shaders
uniform sampler2D image;
in vec2 vTexCoord;
out vec4 fragColor;

void main() {
    vec3 lightdir = texture(image, vTexCoord).rgb;

    fragColor = vec4(lightdir, 1.f);
}
