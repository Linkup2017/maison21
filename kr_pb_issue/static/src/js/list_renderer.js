odoo.define("web.EListRenderer", function(require) {
    "use strict";

    var ListRenderer = require("web.ListRenderer");

    var ERenderer = ListRenderer.include({
        _renderBody: function() {
            var self = this;
            var $rows = this._renderRows();
            var rownum = 4;
            if (this.state.model === "hometax.move.sum") {
                rownum = 1;
            }
            while ($rows.length < rownum) {
                $rows.push(self._renderEmptyRow());
            }
            return $("<tbody>").append($rows);
        }
    });

    return ERenderer;
});
