/*jshint esversion: 6 */

import moment from 'moment';

const utilities = {
    _parseIsoDateStr: function(dateStr) {
        return new moment(dateStr).utc();
    },
    _toIsoDateStr: function(date) {
        return moment.utc(date).format();
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
