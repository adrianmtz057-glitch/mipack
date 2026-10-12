package com.mipack.cliente;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.Mth;

/** Como se mueven y se ven las particulas de Khaset (las texturas las dibuja taller/particulas.py). */
public final class ParticulasCliente {
    private ParticulasCliente() {
    }

    public enum Tipo { VENENO, SANGRE, BRASA, PLUMA, CENIZA }

    public static final class Proveedor implements ParticleProvider<SimpleParticleType> {
        private final SpriteSet sprites;
        private final Tipo tipo;

        public Proveedor(SpriteSet sprites, Tipo tipo) {
            this.sprites = sprites;
            this.tipo = tipo;
        }

        @Override
        public Particle createParticle(SimpleParticleType t, ClientLevel nivel, double x, double y, double z, double dx, double dy, double dz) {
            return new Una(nivel, x, y, z, dx, dy, dz, this.sprites, this.tipo);
        }
    }

    static final class Una extends TextureSheetParticle {
        private final SpriteSet sprites;
        private final Tipo tipo;
        private final float giroMece;

        Una(ClientLevel nivel, double x, double y, double z, double dx, double dy, double dz, SpriteSet sprites, Tipo tipo) {
            super(nivel, x, y, z, 0, 0, 0);
            this.sprites = sprites;
            this.tipo = tipo;
            this.giroMece = this.random.nextFloat() * 6.28f;
            this.xd = dx;
            this.yd = dy;
            this.zd = dz;
            switch (tipo) {
                case VENENO -> {
                    this.lifetime = 22 + this.random.nextInt(14);
                    this.gravity = -0.015f;
                    this.friction = 0.94f;
                    this.quadSize = 0.22f + this.random.nextFloat() * 0.18f;
                    this.xd += (this.random.nextDouble() - 0.5) * 0.03;
                    this.zd += (this.random.nextDouble() - 0.5) * 0.03;
                }
                case SANGRE -> {
                    this.lifetime = 16 + this.random.nextInt(8);
                    this.gravity = 0.7f;
                    this.friction = 0.98f;
                    this.quadSize = 0.07f + this.random.nextFloat() * 0.05f;
                }
                case BRASA -> {
                    this.lifetime = 18 + this.random.nextInt(24);
                    this.gravity = -0.04f;
                    this.friction = 0.92f;
                    this.quadSize = 0.06f + this.random.nextFloat() * 0.07f;
                }
                case PLUMA -> {
                    this.lifetime = 50 + this.random.nextInt(30);
                    this.gravity = 0.025f;
                    this.friction = 0.9f;
                    this.quadSize = 0.18f + this.random.nextFloat() * 0.08f;
                    this.roll = this.random.nextFloat() * 6.28f;
                }
                case CENIZA -> {
                    this.lifetime = 30 + this.random.nextInt(30);
                    this.gravity = 0.006f;
                    this.friction = 0.95f;
                    this.quadSize = 0.05f + this.random.nextFloat() * 0.05f;
                }
            }
            this.hasPhysics = tipo == Tipo.SANGRE || tipo == Tipo.PLUMA;
            elegirSprite();
        }

        private void elegirSprite() {
            if (this.tipo == Tipo.BRASA || this.tipo == Tipo.CENIZA)
                this.setSprite(this.sprites.get(this.random.nextInt(3), 2));
            else if (this.tipo == Tipo.SANGRE)
                this.setSprite(this.sprites.get(this.onGround ? 2 + Math.min(1, (this.age / 4) % 2) : this.yd < -0.05 ? 1 : 0, 3));
            else
                this.setSpriteFromAge(this.sprites);
        }

        @Override
        public void tick() {
            super.tick();
            if (this.tipo == Tipo.PLUMA) {
                this.oRoll = this.roll;
                this.roll += 0.05f * Mth.sin(this.age * 0.15f + this.giroMece);
                this.xd += 0.004 * Mth.sin(this.age * 0.18f + this.giroMece);
                this.zd += 0.004 * Mth.cos(this.age * 0.18f + this.giroMece);
            }
            if (this.tipo == Tipo.VENENO || this.tipo == Tipo.CENIZA)
                this.alpha = Mth.clamp(1f - (float) this.age / this.lifetime, 0f, 1f);
            if (this.tipo == Tipo.BRASA && this.age % 3 == 0)
                elegirSprite();
            if (this.tipo != Tipo.BRASA && this.tipo != Tipo.CENIZA)
                elegirSprite();
        }

        @Override
        public ParticleRenderType getRenderType() {
            return ParticleRenderType.PARTICLE_SHEET_TRANSLUCENT;
        }

        @Override
        protected int getLightColor(float parcial) {
            if (this.tipo == Tipo.BRASA || (this.tipo == Tipo.PLUMA && this.age > this.lifetime / 3))
                return 0xF000F0;
            return super.getLightColor(parcial);
        }
    }
}
