export function parseIsoDateStr(dateStr) {
    /*
    * Converts iso8601 date string to time date in local time
    */
    if (dateStr instanceof Date )
        dateStr = toISODateStr(dateStr);
    return new Date(dateStr);
}

export function toIsoDateStr(date) {
    /*
    * Returns a iso8601 string of a date in local time
    */
    if (date) {
        if (!(date instanceof Date))
            date = parseIsoDateStr(date);
        let pad = function(num) {
            var norm = Math.floor(Math.abs(num));
            return (norm < 10 ? '0' : '') + norm;
        };
        return date.getFullYear() +
            '-' + pad(date.getMonth() + 1) +
            '-' + pad(date.getDate()) +
            'T' + pad(date.getHours()) +
            ':' + pad(date.getMinutes()) +
            ':' + pad(date.getSeconds());
    }
}
