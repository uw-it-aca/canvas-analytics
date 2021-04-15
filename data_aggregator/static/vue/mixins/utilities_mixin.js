import utilities from "../../js/utilities.js";

const utilitiesMixin = {
    filters: {
        short_date: function(date) {
            return utilities.toIsoDateStr(date).split("T")[0].replaceAll("-", "/");
        },
        iso_date: function(date) {
            let iso_date = '';
            if(date) {
                iso_date = utilities.toIsoDateStr(date);
            }
            return iso_date;
        }
    },
}

export default utilitiesMixin;
    