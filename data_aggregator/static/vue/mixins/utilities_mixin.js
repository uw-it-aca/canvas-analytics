const parseIsoDate = function(dateStr) {
    /*
    * Converts iso8601 date string to time date in local time
    */
    if (dateStr instanceof Date )
        dateStr = toIsoDate(dateStr)
    return new Date(dateStr);
}

const toIsoDate = function(date) {
    /*
    * Returns a iso8601 string of a date in local time
    */
    if (date) {
        if (!(date instanceof Date))
            date = parseIsoDate(date)
        let pad = function(num) {
            var norm = Math.floor(Math.abs(num));
            return (norm < 10 ? '0' : '') + norm;
        };
        return date.getFullYear() +
            '-' + pad(date.getMonth() + 1) +
            '-' + pad(date.getDate()) +
            'T' + pad(date.getHours()) +
            ':' + pad(date.getMinutes()) +
            ':' + pad(date.getSeconds())
    }
}

const utilitiesMixin = {
    filters: {
        short_date: function(date) {
            return toIsoDate(date).split("T")[0]
        },
        iso_date: function(date) {
            let iso_date = '';
            if(date) {
                iso_date = toIsoDate(date);
            }
            return iso_date;
        }
    },
    methods: {
        toShortDateStr: function(date) {
            if (date)
                return toIsoDate(date).split("T")[0]
        },
        toISODateStr: function(date) {
            if (date)
                return toIsoDate(date);
        },
        parseIsoDate: function(date) {
            return parseIsoDate(date);
        },
    }
}

export default utilitiesMixin;
    