odoo.define("linkup.buttonRenderer", function(require) {
    "use strict";
    var Dialog = require("web.Dialog");
    var core = require("web.core");
    var FormController = require("web.FormController");
    var _t = core._t;
    FormController.include({
        init: function(parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.linkup_parent = parent;
            this.linkup_model = model;
            this.linkup_renderer = renderer;
            this.linkup_params = params;
        },

        getState: function() {
            const state = this._super.apply(this, arguments);

            if (
                this.initialState.model === "hometax.move" &&
                this.linkup_renderer.state.data.state !== "draft"
            ) {
                setTimeout(function() {
                    $(".o_form_button_edit").hide();
                }, 200);
            } else {
                setTimeout(function() {
                    $(".o_form_button_edit").show();
                }, 200);
            }
            return state;
        },
        _getActionMenuItems: function(state) {
            if (!this.hasActionMenus || this.mode === "edit") {
                return null;
            }
            const props = this._super(...arguments);
            const activeField = this.model.getActiveField(state);
            const otherActionItems = [];
            if (this.archiveEnabled && activeField in state.data) {
                if (state.data[activeField]) {
                    otherActionItems.push({
                        description: _t("Archive"),
                        callback: () => {
                            Dialog.confirm(
                                this,
                                _t(
                                    "Are you sure that you want to archive this record?"
                                ),
                                {
                                    confirm_callback: () =>
                                        this._toggleArchiveState(true)
                                }
                            );
                        }
                    });
                } else {
                    otherActionItems.push({
                        description: _t("Unarchive"),
                        callback: () => this._toggleArchiveState(false)
                    });
                }
            }
            if (this.activeActions.create && this.activeActions.duplicate) {
                otherActionItems.push({
                    description: _t("Duplicate"),
                    callback: () => this._onDuplicateRecord(this)
                });
            }
            if (
                this.initialState.model === "hometax.move" &&
                this.linkup_renderer.state.data.state !== "draft"
            ) {
                console.log("--delete skip");
            } else if (this.activeActions.delete) {
                otherActionItems.push({
                    description: _t("Delete"),
                    callback: () => this._onDeleteRecord(this)
                });
            }
            return Object.assign(props, {
                items: Object.assign(this.toolbarActions, {
                    other: otherActionItems
                })
            });
        }
    });
});
