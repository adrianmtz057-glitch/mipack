package com.mipack.agua;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;

import javax.annotation.Nullable;
import java.util.List;

/**
 * La cantimplora: varios sorbos de agua (cada uno da un buen trago); se llena mirando cualquier agua con clic
 * derecho. La reforzada (con grasa del ballenato) lleva mas sorbos.
 */
public class Cantimplora extends Item {
    private static final String SORBOS = "sorbos";
    private final int maximo;

    public Cantimplora(Properties p, int maximo) {
        super(p.stacksTo(1));
        this.maximo = maximo;
    }

    public int sorbos(ItemStack s) {
        return s.hasTag() ? s.getTag().getInt(SORBOS) : 0;
    }

    public void poner(ItemStack s, int n) {
        s.getOrCreateTag().putInt(SORBOS, Math.max(0, Math.min(maximo, n)));
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level nivel, Player p, InteractionHand mano) {
        ItemStack s = p.getItemInHand(mano);
        BlockHitResult hit = getPlayerPOVHitResult(nivel, p, ClipContext.Fluid.SOURCE_ONLY);
        boolean agua = hit.getType() == HitResult.Type.BLOCK && nivel.getFluidState(hit.getBlockPos()).is(FluidTags.WATER);
        if (agua && sorbos(s) < maximo) {
            if (!nivel.isClientSide) {
                poner(s, maximo);
                nivel.playSound(null, p.blockPosition(), SoundEvents.BOTTLE_FILL, SoundSource.PLAYERS, 1.0f, 0.9f);
            }
            return InteractionResultHolder.sidedSuccess(s, nivel.isClientSide);
        }
        if (sorbos(s) > 0) {
            p.startUsingItem(mano);
            return InteractionResultHolder.consume(s);
        }
        return InteractionResultHolder.fail(s);
    }

    @Override
    public ItemStack finishUsingItem(ItemStack s, Level nivel, LivingEntity quien) {
        if (quien instanceof Player p && !nivel.isClientSide && sorbos(s) > 0) {
            Agua.beber(p, 6.0f);
            if (!p.getAbilities().instabuild)
                poner(s, sorbos(s) - 1);
        }
        return s;
    }

    @Override
    public UseAnim getUseAnimation(ItemStack s) {
        return UseAnim.DRINK;
    }

    @Override
    public int getUseDuration(ItemStack s) {
        return 24;
    }

    @Override
    public boolean isBarVisible(ItemStack s) {
        return true;
    }

    @Override
    public int getBarWidth(ItemStack s) {
        return Math.round(13.0f * sorbos(s) / maximo);
    }

    @Override
    public int getBarColor(ItemStack s) {
        return 0x3FA9F5;
    }

    @Override
    public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
        lineas.add(Component.translatable("item.mipack.cantimplora.sorbos", sorbos(s), maximo).withStyle(ChatFormatting.AQUA));
        lineas.add(Component.translatable("item.mipack.cantimplora.ayuda").withStyle(ChatFormatting.GRAY));
    }
}
