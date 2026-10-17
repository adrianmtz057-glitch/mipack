#version 150

// La mezcla final: ondas de calor, neblina de distancia, brillo suave, rayos de sol, tono de la hora y vineta.
uniform sampler2D Sampler0;
uniform sampler2D DepthSampler;
uniform sampler2D BloomSampler;

uniform vec3 Tinte;
uniform vec3 Sombras;
uniform vec3 Luces;
uniform float Saturacion;
uniform float Contraste;
uniform float BloomFuerza;
uniform vec2 SolPos;
uniform float SolFuerza;
uniform vec3 SolColor;
uniform vec3 Neblina;
uniform float NeblinaFuerza;
uniform float Lejos;
uniform float Calor;
uniform float Tiempo;
uniform float Vineta;
uniform float Aspecto;

in vec2 texCoord;
out vec4 fragColor;

float distancia(float d) {
    float n = 0.05;
    float z = d * 2.0 - 1.0;
    return 2.0 * n * Lejos / (Lejos + n - z * (Lejos - n));
}

void main() {
    vec2 uv = texCoord;
    float d0 = texture(DepthSampler, uv).r;
    bool cielo = d0 >= 0.99999;
    float dist = cielo ? Lejos : distancia(d0);

    // el aire caliente del desierto: lo lejano ondula
    if (Calor > 0.001) {
        float k = Calor * smoothstep(24.0, 80.0, dist);
        uv.x += sin(uv.y * 210.0 + Tiempo * 5.0) * 0.0010 * k;
        uv.y += sin(uv.x * 150.0 + Tiempo * 3.7) * 0.0006 * k;
    }
    vec3 c = texture(Sampler0, uv).rgb;

    // perspectiva de aire: lo lejano se aclara hacia el color del horizonte
    if (!cielo)
        c = mix(c, Neblina, NeblinaFuerza * smoothstep(20.0, Lejos * 0.85, dist));

    // brillo suave
    c += texture(BloomSampler, uv).rgb * BloomFuerza;

    // rayos de sol: desde cada pixel hacia el sol, cuanto cielo se ve en el camino
    // (solo cuenta el cielo junto al sol: asi salen franjas que se cortan en lo que lo tapa)
    if (SolFuerza > 0.001) {
        const int PASOS = 40;
        vec2 paso = (SolPos - texCoord) / float(PASOS);
        vec2 p = texCoord;
        float luz = 0.0, peso = 1.0;
        for (int i = 0; i < PASOS; i++) {
            p += paso;
            vec2 q = clamp(p, 0.001, 0.999);
            float visto = texture(DepthSampler, q).r >= 0.99999 ? 1.0 : 0.0;
            float junto = 1.0 - smoothstep(0.0, 0.22, distance(q * vec2(Aspecto, 1.0), SolPos * vec2(Aspecto, 1.0)));
            luz += visto * junto * junto * peso;
            peso *= 0.968;
        }
        luz /= float(PASOS);
        float cerca = 1.0 - smoothstep(0.0, 1.1, distance(texCoord * vec2(Aspecto, 1.0), SolPos * vec2(Aspecto, 1.0)));
        c += SolColor * luz * cerca * SolFuerza * 2.6;
    }

    // el tono de la hora: sombras y luces de distinto color
    float lum = dot(c, vec3(0.299, 0.587, 0.114));
    c *= mix(Sombras, Luces, smoothstep(0.08, 0.85, lum));
    c *= Tinte;
    c = (c - 0.5) * Contraste + 0.5;
    lum = dot(c, vec3(0.299, 0.587, 0.114));
    c = mix(vec3(lum), c, Saturacion);

    // vineta suave
    float v = smoothstep(0.42, 1.1, length((texCoord - 0.5) * vec2(Aspecto, 1.0)) * 1.25);
    c *= 1.0 - Vineta * v;

    fragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
}
