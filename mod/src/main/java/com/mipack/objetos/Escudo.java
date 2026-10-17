package com.mipack.objetos;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ShieldItem;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;

import javax.annotation.Nullable;
import java.util.List;
import java.util.function.Consumer;
import java.util.function.Supplier;

/**
 * Los escudos de los drops: el de escamas (aguanta mucho mas que el de madera) y el de caparazon (ligero: al cubrirte
 * casi no te alentas; ver ClienteObjetos). Se dibujan con el modelo del escudo de Minecraft y su propia textura
 * (textures/entity/escudo/{id}.png).
 */
public class Escudo extends ShieldItem {
    private final String id;
    private final boolean ligero;
    private final Supplier<Item> reparar;

    public Escudo(Properties p, String id, boolean ligero, Supplier<Item> reparar) {
        super(p);
        this.id = id;
        this.ligero = ligero;
        this.reparar = reparar;
    }

    public String id() {
        return id;
    }

    public boolean ligero() {
        return ligero;
    }

    @Override
    public boolean isValidRepairItem(ItemStack s, ItemStack con) {
        return con.is(reparar.get());
    }

    @Override
    public String getDescriptionId(ItemStack s) {
        return getDescriptionId();
    }

    @Override
    public void appendHoverText(ItemStack s, @Nullable Level l, List<Component> lineas, TooltipFlag f) {
        ObjetosSimples.ayuda(lineas, getDescriptionId() + ".ayuda");
    }

    @Override
    public void initializeClient(Consumer<IClientItemExtensions> consumidor) {
        consumidor.accept(new IClientItemExtensions() {
            private BlockEntityWithoutLevelRenderer r;

            @Override
            public BlockEntityWithoutLevelRenderer getCustomRenderer() {
                if (r == null)
                    r = new com.mipack.cliente.RenderEscudo(Minecraft.getInstance().getBlockEntityRenderDispatcher(),
                            Minecraft.getInstance().getEntityModels());
                return r;
            }
        });
    }
}
