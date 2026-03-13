/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {SelectionField} from "@web/views/fields/selection/selection_field";

patch(SelectionField.prototype, {
    get options() {
        const allOptions = super.options;
        return allOptions.filter(([value, label]) => label !== "Select Role");
    }
});