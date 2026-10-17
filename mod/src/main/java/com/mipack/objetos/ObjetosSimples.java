package com.mipack.objetos;

import com.mipack.agua.Agua;
import com.mipack.khaset.EfectosKhaset;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.entity.projectile.Arrow;
import net.minecraft.world.item.ArrowItem;
import net.minecraft.world.item.BoneMealItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tier;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.level.Level;
import net.minecraftforge.registries.RegistryObject;

import javax.annotation.Nullable;
import java.util.List;
import java.util.Optional;
import java.util.function.Supplier;

/** Los objetos sencillos: armas de los drops, comida, el fertilizante, la runa de Pibble y las varitas. */
public final class ObjetosSimples {
    private ObjetosSimples() {
    }

    /** Un material de herramienta propio (cuanto dura, que tanto pega, con que se repara). */
    public record Material(int usos, float velocidad, float dano, int nivel, int encantable,
                           Supplier<RegistryObject<Item>> reparar) implements Tier {
        @Override
        public int getUses() {
            return usos;
        }

        @Override
        public float getSpeed() {
            return velocidad;
        }

        @Override
        public float getAttackDamageBonus() {
            return dano;
        }

        @Override
        public int getLevel() {
            return nivel;
        }

        @Override
        public int getEnchantmentValue() {
            return encantable;
        }

        @Override
        public Ingredient getRepairIngredient() {
            return Ingredient.of(reparar.get().get());
        }
    }

    static void ayuda(List<Component> lineas, String clave) {
        lineas.add(Component.translatable(clave).withStyle(ChatFormatting.GRAY));
    }

    /** Daga de colmillo: rapida y corta (desangra un poco). */
    public static final class Daga extends SwordItem {
        public Daga(Tier t, Properties p) {
            super(t, 2, -1.6f, p);
        }

        @Override
        public boolean hurtEnemy(ItemStack stack, LivingEntity blanco, LivingEntity quien) {
            if (!blanco.level().isClientSide && quien.getRandom().nextFloat() < 0.35f)
                blanco.addEffect(new MobEffectInstance(EfectosKhaset.DESANGRADO.get(), 80, 0));
            return super.hurtEnemy(stack, blanco, quien);
        }

        @Override
        public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
            ayuda(lineas, "item.mipack.daga_colmillo.ayuda");
        }
    }

    /** Martillo de cuerno: lento y pesado, avienta lejos. */
    public static final class Martillo extends SwordItem {
        public Martillo(Tier t, Properties p) {
            super(t, 6, -3.3f, p);
        }

        @Override
        public boolean hurtEnemy(ItemStack stack, LivingEntity blanco, LivingEntity quien) {
            double dx = blanco.getX() - quien.getX(), dz = blanco.getZ() - quien.getZ();
            double d = Math.max(0.01, Math.sqrt(dx * dx + dz * dz));
            blanco.knockback(1.2, -dx / d, -dz / d);
            return super.hurtEnemy(stack, blanco, quien);
        }

        @Override
        public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
            ayuda(lineas, "item.mipack.martillo_cuerno.ayuda");
        }
    }

    /** Flecha de aguijon: alenta al que pica. */
    public static final class FlechaAguijon extends ArrowItem {
        public FlechaAguijon(Properties p) {
            super(p);
        }

        @Override
        public AbstractArrow createArrow(Level nivel, ItemStack stack, LivingEntity tirador) {
            Arrow a = new Arrow(nivel, tirador);
            a.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 120, 1));
            return a;
        }
    }

    /** Comida que ademas da (o quita) agua; la carne salada tambien quita el hambre (el efecto). */
    public static final class Comida extends Item {
        private final float agua;
        private final boolean curaHambre;

        public Comida(Properties p, float agua, boolean curaHambre) {
            super(p);
            this.agua = agua;
            this.curaHambre = curaHambre;
        }

        @Override
        public ItemStack finishUsingItem(ItemStack stack, Level nivel, LivingEntity quien) {
            if (quien instanceof Player p) {
                if (agua != 0)
                    Agua.beber(p, agua);
                if (curaHambre)
                    p.removeEffect(MobEffects.HUNGER);
            }
            return super.finishUsingItem(stack, nivel, quien);
        }

        @Override
        public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
            ayuda(lineas, getDescriptionId() + ".ayuda");
        }
    }

    /** Fertilizante de musgo: como harina de hueso pero fuerte, en un cuadro de 3x3 y varias veces. */
    public static final class Fertilizante extends Item {
        public Fertilizante(Properties p) {
            super(p);
        }

        @Override
        public InteractionResult useOn(UseOnContext c) {
            Level nivel = c.getLevel();
            BlockPos centro = c.getClickedPos();
            boolean algo = false;
            for (BlockPos pos : BlockPos.betweenClosed(centro.offset(-1, -1, -1), centro.offset(1, 1, 1))) {
                for (int k = 0; k < 3; k++) {
                    ItemStack prueba = new ItemStack(net.minecraft.world.item.Items.BONE_MEAL);
                    if (BoneMealItem.applyBonemeal(prueba, nivel, pos.immutable(), c.getPlayer())) {
                        algo = true;
                        if (!nivel.isClientSide)
                            nivel.levelEvent(1505, pos.immutable(), 0);
                    }
                }
            }
            if (algo && !nivel.isClientSide && (c.getPlayer() == null || !c.getPlayer().getAbilities().instabuild))
                c.getItemInHand().shrink(1);
            return algo ? InteractionResult.sidedSuccess(nivel.isClientSide) : InteractionResult.PASS;
        }

        @Override
        public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
            ayuda(lineas, "item.mipack.fertilizante_musgo.ayuda");
        }
    }

    /** Runa de Pibble: te lleva a donde moriste por ultima vez (se gasta). */
    public static final class Runa extends Item {
        public Runa(Properties p) {
            super(p);
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level nivel, Player p, InteractionHand mano) {
            ItemStack stack = p.getItemInHand(mano);
            if (!(p instanceof ServerPlayer sp))
                return InteractionResultHolder.success(stack);
            Optional<GlobalPos> donde = sp.getLastDeathLocation();
            if (donde.isEmpty()) {
                sp.displayClientMessage(Component.translatable("item.mipack.runa_pibble.nada"), true);
                return InteractionResultHolder.fail(stack);
            }
            ServerLevel destino = sp.server.getLevel(donde.get().dimension());
            if (destino == null)
                return InteractionResultHolder.fail(stack);
            BlockPos b = donde.get().pos();
            ((ServerLevel) nivel).sendParticles(ParticleTypes.REVERSE_PORTAL, p.getX(), p.getY() + 1, p.getZ(), 40, 0.4, 0.8, 0.4, 0.05);
            sp.teleportTo(destino, b.getX() + 0.5, b.getY(), b.getZ() + 0.5, sp.getYRot(), sp.getXRot());
            destino.playSound(null, b, SoundEvents.ENDERMAN_TELEPORT, SoundSource.PLAYERS, 1.0f, 0.8f);
            destino.sendParticles(ParticleTypes.REVERSE_PORTAL, b.getX() + 0.5, b.getY() + 1, b.getZ() + 0.5, 40, 0.4, 0.8, 0.4, 0.05);
            if (!sp.getAbilities().instabuild)
                stack.shrink(1);
            return InteractionResultHolder.consume(stack);
        }

        @Override
        public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
            ayuda(lineas, "item.mipack.runa_pibble.ayuda");
        }
    }

    /**
     * Varitas de estrella: la de Revolthir (caos) le pone un efecto al azar, bueno o malo, a lo que golpea; la de
     * Correctar (orden) le quita todos los efectos a lo que golpea, y con clic derecho te los quita a ti.
     */
    public static final class Varita extends Item {
        private static final MobEffect[] AZAR = {MobEffects.MOVEMENT_SPEED, MobEffects.MOVEMENT_SLOWDOWN, MobEffects.JUMP,
                MobEffects.LEVITATION, MobEffects.GLOWING, MobEffects.CONFUSION, MobEffects.REGENERATION, MobEffects.WEAKNESS,
                MobEffects.DAMAGE_BOOST, MobEffects.BLINDNESS, MobEffects.INVISIBILITY, MobEffects.POISON};
        private final boolean caos;

        public Varita(Properties p, boolean caos) {
            super(p);
            this.caos = caos;
        }

        @Override
        public boolean hurtEnemy(ItemStack stack, LivingEntity blanco, LivingEntity quien) {
            if (caos) {
                RandomSource r = quien.getRandom();
                blanco.addEffect(new MobEffectInstance(AZAR[r.nextInt(AZAR.length)], 120, r.nextInt(2)));
            } else {
                blanco.removeAllEffects();
            }
            stack.hurtAndBreak(1, quien, q -> q.broadcastBreakEvent(InteractionHand.MAIN_HAND));
            return true;
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level nivel, Player p, InteractionHand mano) {
            ItemStack stack = p.getItemInHand(mano);
            if (caos)
                return InteractionResultHolder.pass(stack);
            if (!nivel.isClientSide) {
                p.removeAllEffects();
                p.getCooldowns().addCooldown(this, 600);
                stack.hurtAndBreak(2, p, q -> q.broadcastBreakEvent(mano));
                nivel.playSound(null, p.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0f, 1.4f);
            }
            return InteractionResultHolder.sidedSuccess(stack, nivel.isClientSide);
        }

        @Override
        public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
            ayuda(lineas, getDescriptionId() + ".ayuda");
        }
    }
}
