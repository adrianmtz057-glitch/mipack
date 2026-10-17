package com.mipack.objetos;

import com.mipack.Mipack;
import net.minecraft.ChatFormatting;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;
import software.bernie.geckolib.animatable.GeoItem;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.model.GeoModel;
import software.bernie.geckolib.renderer.GeoArmorRenderer;
import software.bernie.geckolib.util.GeckoLibUtil;

import javax.annotation.Nullable;
import java.util.List;
import java.util.function.Consumer;

/**
 * Una pieza de armadura de Velkia: con su propio modelo de cubos (GeckoLib), no un recolor. Lo que hace cada una lo
 * pone EfectosArmadura; aqui el modelo y la ayuda del tooltip.
 */
public class ArmaduraMipack extends ArmorItem implements GeoItem {
    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);
    private final MaterialArmadura material;

    public ArmaduraMipack(MaterialArmadura material, Type tipo, Properties p) {
        super(material, tipo, p);
        this.material = material;
    }

    public MaterialArmadura material() {
        return material;
    }

    @Override
    public void initializeClient(Consumer<IClientItemExtensions> consumidor) {
        consumidor.accept(new IClientItemExtensions() {
            private GeoArmorRenderer<?> renderer;

            @Override
            public HumanoidModel<?> getHumanoidArmorModel(LivingEntity e, ItemStack s, EquipmentSlot slot, HumanoidModel<?> original) {
                if (renderer == null)
                    renderer = new GeoArmorRenderer<>(new Modelo(material.modelo()));
                renderer.prepForRender(e, s, slot, original);
                return renderer;
            }
        });
    }

    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controles) {
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() {
        return cache;
    }

    @Override
    public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
        lineas.add(Component.translatable("armadura.mipack." + material.modelo()).withStyle(ChatFormatting.GRAY));
    }

    /** El modelo de la armadura: geo/armor/{id}.geo.json y textures/armor/{id}.png (sin animaciones). */
    public static final class Modelo extends GeoModel<ArmaduraMipack> {
        private final ResourceLocation geo, textura;
        private static final ResourceLocation ANIM = new ResourceLocation(Mipack.MODID, "animations/armor/quieta.animation.json");

        Modelo(String id) {
            geo = new ResourceLocation(Mipack.MODID, "geo/armor/" + id + ".geo.json");
            textura = new ResourceLocation(Mipack.MODID, "textures/armor/" + id + ".png");
        }

        @Override
        public ResourceLocation getModelResource(ArmaduraMipack a) {
            return geo;
        }

        @Override
        public ResourceLocation getTextureResource(ArmaduraMipack a) {
            return textura;
        }

        @Override
        public ResourceLocation getAnimationResource(ArmaduraMipack a) {
            return ANIM;
        }
    }
}
