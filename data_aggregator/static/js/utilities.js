/*jshint esversion: 6 */

const utilities = {
    _parseIsoDateStr: function(dateStr) {
        return new Date(dateStr);
    },
    _toIsoDateStr: function(date) {
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
    },
    parseIsoDateStr: function(dateStr) {
        /*
        * Converts iso8601 date string to time date in local time
        */
        if(dateStr) {
            if (dateStr instanceof Date )
                dateStr = this._toIsoDateStr(dateStr);
            return this._parseIsoDateStr(dateStr);
        }
    },
    toIsoDateStr: function(date) {
        /*
        * Returns a iso8601 string of a date in local time
        */
        if (date) {
            if (!(date instanceof Date))
                date = this._parseIsoDateStr(date);
            return this._toIsoDateStr(date);
        }
    },
    countByProperty: function(dictList, property) {
        let groupedByProperty = {};
        dictList.forEach(item => {
            if(property in item) {
                if (item[property] in groupedByProperty) {
                    groupedByProperty[item[property]] += 1;
                } else {
                    groupedByProperty[item[property]] = 1;
                }
            }
        });
        return groupedByProperty;
    }
};

export default utilities;
