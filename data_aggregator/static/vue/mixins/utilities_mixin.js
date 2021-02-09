import {parseIsoDateStr, toIsoDateStr} from "../../js/utilities.js";

const utilitiesMixin = {
    filters: {
        short_date: function(date) {
            return toIsoDateStr(date).split("T")[0]
        },
        iso_date: function(date) {
            let iso_date = '';
            if(date) {
                iso_date = toIsoDateStr(date);
            }
            return iso_date;
        }
    },
}

export default utilitiesMixin;
    