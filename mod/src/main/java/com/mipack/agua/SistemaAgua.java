package com.mipack.agua;

import com.mipack.Mipack;
import com.mipack.objetos.EfectosObjetos;
import com.mipack.objetos.MaterialArmadura;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.ArmorMaterials;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.alchemy.PotionUtils;
import net.minecraft.world.item.alchemy.Potions;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.Tags;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingEntityUseItemEvent;
import net.minecraftforge.event.entity.player.AttackEntityEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.entity.player.PlayerInteractEvent;
import net.minecraftforge.event.level.BlockEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.ForgeRegistries;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * La sed y el frio.
 * <ul>
 * <li>El agua siempre baja: la barra dura {@code minutos_fuera}; en los biomas frescos (la lista
 *     {@code biomas_frescos}: montanas, jardines) dura mas, {@code minutos_fresco}. En los biomas calientes (la lista
 *     {@code biomas_calientes}: desierto, volcan, canon, sales) la Sofocacion esta siempre y la barra dura
 *     {@code minutos_desierto}, dividido entre lo que sofoca la armadura (pieza por pieza, cada una con su peso:
 *     diamante completo sofoca el doble, netherita el triple) y nunca menos de {@code minutos_minimo}. La armadura del
 *     desierto no sofoca. De noche la armadura no pesa y a la sombra pesa la mitad; el pedazo de piramide en la mano
 *     tambien la baja a la mitad.</li>
 * <li>Se toma agua de: la cantimplora, las botellas de agua, el rio (agachado, clic derecho con la mano vacia), la
 *     lluvia (estando afuera) y algunas comidas (la pulpa de cactus, la sandia, la leche, los guisos...).</li>
 * <li>En cero te desmayas: no te puedes mover ni hacer nada (el chat si) por {@code segundos_desmayo}, la pantalla se
 *     va a negro, y despiertas con un poco de agua. Los mobs si te pueden pegar.</li>
 * <li>Los nuevos tienen {@code minutos_gracia} sin sed.</li>
 * <li>El frio: en lugares donde nieva, lejos del fuego, la comida se va mas rapido (efecto Frio) segun cuanto abrigo
 *     de pelaje traigas.</li>
 * </ul>
 */
@Mod.EventBusSubscriber(modid = Mipack.MODID)
public final class SistemaAgua {
    static final String DESMAYO = "mipack_desmayo", DESMAYO_TOTAL = "mipack_desmayo_total", JUGADO = "mipack_jugado";
    private static final UUID QUIETO = UUID.fromString("5b0c6f3e-2a1d-4c8e-9e47-8d2a3f1c0b77");
    /** Lo que pesa cada pieza en la sofocacion y en el abrigo (suman 1). */
    private static final Map<EquipmentSlot, Float> PESO = Map.of(EquipmentSlot.HEAD, 0.15f, EquipmentSlot.CHEST, 0.40f,
            EquipmentSlot.LEGS, 0.30f, EquipmentSlot.FEET, 0.15f);
    private static final Map<UUID, RedAgua.Estado> ENVIADO = new HashMap<>();
    private static final Map<UUID, Long> ULTIMO_SORBO = new HashMap<>();
    private static final ResourceLocation PIRAMIDE = new ResourceLocation(Mipack.MODID, "pedazo_piramide");

    private SistemaAgua() {
    }

    static boolean activa(Player p) {
        return ConfigAgua.ACTIVA.get() && !p.isCreative() && !p.isSpectator();
    }

    public static boolean desmayado(Player p) {
        return p.getPersistentData().getInt(DESMAYO) > 0;
    }

    // ------------------------------------------------------------------ cuanto sofoca la armadura

    /** Lo que sofoca una pieza (1 = nada; la de diamante 2, la de netherita 3; la del desierto menos de 1). */
    static float calor(ItemStack s) {
        if (!(s.getItem() instanceof ArmorItem a))
            return 1.0f;
        ArmorMaterial m = a.getMaterial();
        if (m instanceof MaterialArmadura mm)
            return mm.calor();
        if (m == ArmorMaterials.LEATHER)
            return 1.15f;
        if (m == ArmorMaterials.GOLD)
            return 1.25f;
        if (m == ArmorMaterials.TURTLE)
            return 1.3f;
        if (m == ArmorMaterials.CHAIN)
            return 1.35f;
        if (m == ArmorMaterials.IRON)
            return 1.5f;
        if (m == ArmorMaterials.DIAMOND)
            return 2.0f;
        if (m == ArmorMaterials.NETHERITE)
            return 3.0f;
        return 1.0f + 0.12f * a.getDefense();
    }

    /** Cuanto sofoca todo lo que trae puesto (1 = nada). */
    public static float sofocacion(Player p) {
        float f = 1.0f;
        for (Map.Entry<EquipmentSlot, Float> e : PESO.entrySet())
            f += e.getValue() * (calor(p.getItemBySlot(e.getKey())) - 1.0f);
        return Math.max(0.5f, f);
    }

    /** Cuanto abrigo de pelaje trae (0 a 1). */
    public static float abrigo(Player p) {
        float f = 0.0f;
        for (Map.Entry<EquipmentSlot, Float> e : PESO.entrySet()) {
            ItemStack s = p.getItemBySlot(e.getKey());
            if (s.getItem() instanceof ArmorItem a && a.getMaterial() instanceof MaterialArmadura m)
                f += e.getValue() * m.abrigo();
        }
        return Math.min(1.0f, f);
    }

    /** Si el bioma esta en la lista (ids "minecraft:desert" o etiquetas "#minecraft:is_badlands"). */
    static boolean es(net.minecraft.core.Holder<net.minecraft.world.level.biome.Biome> bioma, java.util.List<? extends String> lista) {
        for (String e : lista) {
            if (e.startsWith("#")) {
                ResourceLocation rl = ResourceLocation.tryParse(e.substring(1));
                if (rl != null && bioma.is(net.minecraft.tags.TagKey.create(net.minecraft.core.registries.Registries.BIOME, rl)))
                    return true;
            } else {
                ResourceLocation rl = ResourceLocation.tryParse(e);
                if (rl != null && bioma.unwrapKey().map(k -> k.location().equals(rl)).orElse(false))
                    return true;
            }
        }
        return false;
    }

    static boolean conPiramide(Player p) {
        return PIRAMIDE.equals(ForgeRegistries.ITEMS.getKey(p.getMainHandItem().getItem()))
                || PIRAMIDE.equals(ForgeRegistries.ITEMS.getKey(p.getOffhandItem().getItem()));
    }

    // ------------------------------------------------------------------ cada tick

    @SubscribeEvent
    public static void tick(TickEvent.PlayerTickEvent e) {
        if (e.phase != TickEvent.Phase.END || e.player.level().isClientSide)
            return;
        Player p = e.player;
        CompoundTag d = p.getPersistentData();
        int desmayo = d.getInt(DESMAYO);
        if (desmayo > 0) {
            d.putInt(DESMAYO, desmayo - 1);
            if (desmayo - 1 == 0)
                despertar(p);
            if (desmayo % 10 == 0)
                avisar(p);
            return;
        }
        if (!activa(p)) {
            if (p.tickCount % 40 == 0)
                avisar(p);
            return;
        }
        CompoundTag siempre = d.getCompound(Player.PERSISTED_NBT_TAG);        // la gracia no se reinicia al morir
        int jugado = siempre.getInt(JUGADO);
        if (jugado < ConfigAgua.MINUTOS_GRACIA.get() * 1200) {
            siempre.putInt(JUGADO, jugado + 1);
            d.put(Player.PERSISTED_NBT_TAG, siempre);
            if (p.tickCount % 40 == 0)
                avisar(p);
            return;
        }
        if (p.tickCount % 20 != 0)
            return;
        Level nivel = p.level();
        BlockPos pos = p.blockPosition();
        net.minecraft.core.Holder<net.minecraft.world.level.biome.Biome> bioma = nivel.getBiome(pos);
        double minutos = ConfigAgua.MINUTOS_FUERA.get();
        if (es(bioma, ConfigAgua.CALIENTES.get())) {
            float f = sofocacion(p);                             // la armadura: de noche no pesa y a la sombra, la mitad
            if (!nivel.isDay())
                f = Math.min(f, 1.0f);
            else if (!nivel.canSeeSky(pos.above()))
                f = 1.0f + (f - 1.0f) * 0.5f;
            if (conPiramide(p))
                f = 1.0f + (f - 1.0f) * 0.5f;
            minutos = Math.max(ConfigAgua.MINUTOS_MINIMO.get(), ConfigAgua.MINUTOS_DESIERTO.get() / Math.max(f, 0.5f));
            p.addEffect(new MobEffectInstance(EfectosObjetos.SOFOCACION.get(), 60, 0, false, false, true));
        } else if (es(bioma, ConfigAgua.FRESCOS.get())) {
            minutos = ConfigAgua.MINUTOS_FRESCO.get();
        }
        float agua = Agua.agua(p) - (float) (Agua.MAX / (minutos * 60.0));
        if (nivel.isRainingAt(pos.above()))
            agua += 0.25f;
        Agua.poner(p, agua);
        if (agua <= 0.0f)
            desmayar(p);
        if (ConfigAgua.FRIO.get())
            frio(p);
        avisar(p);
    }

    private static void frio(Player p) {
        Level nivel = p.level();
        BlockPos pos = p.blockPosition();
        if (!nivel.getBiome(pos).value().coldEnoughToSnow(pos) || p.isInWater() || cercaDelFuego(nivel, pos))
            return;
        float expuesto = 1.0f - abrigo(p);
        if (expuesto < 0.05f)
            return;
        p.causeFoodExhaustion(0.14f * expuesto);
        p.addEffect(new MobEffectInstance(EfectosObjetos.FRIO.get(), 60, 0, false, false, true));
    }

    private static boolean cercaDelFuego(Level nivel, BlockPos pos) {
        for (BlockPos b : BlockPos.betweenClosed(pos.offset(-3, -2, -3), pos.offset(3, 2, 3))) {
            BlockState s = nivel.getBlockState(b);
            if (s.is(BlockTags.CAMPFIRES) || s.is(BlockTags.FIRE) || s.is(Blocks.LAVA) || s.is(Blocks.MAGMA_BLOCK)
                    || s.is(Blocks.FURNACE) && s.getLightEmission(nivel, b) > 0)
                return true;
        }
        return false;
    }

    // ------------------------------------------------------------------ el desmayo

    static void desmayar(Player p) {
        int ticks = ConfigAgua.SEGUNDOS_DESMAYO.get() * 20;
        p.getPersistentData().putInt(DESMAYO, ticks);
        p.getPersistentData().putInt(DESMAYO_TOTAL, ticks);
        AttributeInstance v = p.getAttribute(Attributes.MOVEMENT_SPEED);
        if (v != null && v.getModifier(QUIETO) == null)
            v.addTransientModifier(new AttributeModifier(QUIETO, "mipack desmayo", -1.0, AttributeModifier.Operation.MULTIPLY_TOTAL));
        p.stopUsingItem();
        p.displayClientMessage(Component.translatable("agua.mipack.desmayo"), true);
        avisar(p);
    }

    static void despertar(Player p) {
        AttributeInstance v = p.getAttribute(Attributes.MOVEMENT_SPEED);
        if (v != null)
            v.removeModifier(QUIETO);
        Agua.poner(p, Math.max(Agua.agua(p), 4.0f));
        avisar(p);
    }

    @SubscribeEvent
    public static void sinPegar(AttackEntityEvent e) {
        if (desmayado(e.getEntity()))
            e.setCanceled(true);
    }

    @SubscribeEvent
    public static void sinUsar(PlayerInteractEvent e) {
        if (e.isCancelable() && desmayado(e.getEntity()))
            e.setCanceled(true);
    }

    @SubscribeEvent
    public static void sinRomper(BlockEvent.BreakEvent e) {
        if (desmayado(e.getPlayer()))
            e.setCanceled(true);
    }

    /** Al reaparecer: sin desmayo y con la velocidad normal (el agua ya vuelve llena: no se copia). */
    @SubscribeEvent
    public static void reaparecer(PlayerEvent.PlayerRespawnEvent e) {
        if (e.getEntity() instanceof ServerPlayer p) {
            AttributeInstance v = p.getAttribute(Attributes.MOVEMENT_SPEED);
            if (v != null)
                v.removeModifier(QUIETO);
            avisar(p);
        }
    }

    @SubscribeEvent
    public static void entrar(PlayerEvent.PlayerLoggedInEvent e) {
        if (e.getEntity() instanceof ServerPlayer p) {
            if (desmayado(p))
                despertar(p);
            p.getPersistentData().putInt(DESMAYO, 0);
            ENVIADO.remove(p.getUUID());
            avisar(p);
        }
    }

    // ------------------------------------------------------------------ tomar agua

    /** Las botellas de agua y algunas comidas dan agua. */
    @SubscribeEvent
    public static void alTerminarDeUsar(LivingEntityUseItemEvent.Finish e) {
        if (!(e.getEntity() instanceof Player p) || p.level().isClientSide)
            return;
        ItemStack s = e.getItem();
        if (s.is(Items.POTION) && PotionUtils.getPotion(s) == Potions.WATER)
            Agua.beber(p, 6.0f);
        else if (s.is(Items.MELON_SLICE))
            Agua.beber(p, 1.5f);
        else if (s.is(Items.MILK_BUCKET))
            Agua.beber(p, 4.0f);
        else if (s.is(Items.MUSHROOM_STEW) || s.is(Items.BEETROOT_SOUP) || s.is(Items.RABBIT_STEW) || s.is(Items.SUSPICIOUS_STEW))
            Agua.beber(p, 2.0f);
        else if (s.is(Items.HONEY_BOTTLE) || s.is(Items.GLOW_BERRIES) || s.is(Items.SWEET_BERRIES))
            Agua.beber(p, 1.0f);
    }

    /** Agachado y con la mano vacia, clic derecho mirando agua: un trago (avisa el cliente; aqui se comprueba). */
    static void beberDelRio(ServerPlayer p) {
        long ahora = p.level().getGameTime();
        Long antes = ULTIMO_SORBO.get(p.getUUID());
        if (antes != null && ahora - antes < 12 || desmayado(p) || !p.getMainHandItem().isEmpty())
            return;
        Vec3 ojo = p.getEyePosition();
        Vec3 fin = ojo.add(p.getViewVector(1.0f).scale(4.5));
        BlockHitResult hit = p.level().clip(new ClipContext(ojo, fin, ClipContext.Block.OUTLINE, ClipContext.Fluid.SOURCE_ONLY, p));
        if (hit.getType() != HitResult.Type.BLOCK || !p.level().getFluidState(hit.getBlockPos()).is(FluidTags.WATER))
            return;
        ULTIMO_SORBO.put(p.getUUID(), ahora);
        Agua.beber(p, 2.0f);
        p.level().playSound(null, p.blockPosition(), SoundEvents.GENERIC_DRINK, SoundSource.PLAYERS, 0.6f, 1.1f);
        Vec3 h = hit.getLocation();
        ((ServerLevel) p.level()).sendParticles(ParticleTypes.SPLASH, h.x, h.y + 0.1, h.z, 6, 0.2, 0.05, 0.2, 0.1);
    }

    // ------------------------------------------------------------------ al cliente

    /** Le manda su agua al jugador si cambio. */
    public static void avisar(Player jugador) {
        if (!(jugador instanceof ServerPlayer p))
            return;
        CompoundTag d = p.getPersistentData();
        RedAgua.Estado e = new RedAgua.Estado(Agua.agua(p), d.getInt(DESMAYO), d.getInt(DESMAYO_TOTAL), activa(p));
        RedAgua.Estado antes = ENVIADO.get(p.getUUID());
        if (antes != null && Math.abs(antes.agua() - e.agua()) < 0.04f && antes.desmayo() == e.desmayo() && antes.activa() == e.activa())
            return;
        ENVIADO.put(p.getUUID(), e);
        RedAgua.enviar(p, e);
    }
}
