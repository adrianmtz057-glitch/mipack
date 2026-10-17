#version 150

// Un cuadro que cubre la pantalla (las esquinas ya vienen de -1 a 1).
in vec3 Position;
in vec2 UV0;

out vec2 texCoord;

void main() {
    gl_Position = vec4(Position.xy, 0.0, 1.0);
    texCoord = UV0;
}
