/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ProductCatalogOrderLine } from "@product/product_catalog/order_line";

patch(ProductCatalogOrderLine.prototype, {
    get resModel() {
        return this.props.record.context.product_catalog_order_model || super.resModel;
    }
});