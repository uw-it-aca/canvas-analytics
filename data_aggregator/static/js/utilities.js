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
    },
    formatDuration: function(period) {
        let parts = [];
        const duration = moment.duration(period);
    
        // return nothing when the duration is falsy or not correctly parsed (P0D)
        if(!duration || duration.toISOString() === "P0D") return;
    
        if(duration.years() >= 1) {
            const years = Math.floor(duration.years());
            parts.push(years+" "+(years > 1 ? "years" : "year"));
        }
    
        if(duration.months() >= 1) {
            const months = Math.floor(duration.months());
            parts.push(months+" "+(months > 1 ? "months" : "month"));
        }
    
        if(duration.days() >= 1) {
            const days = Math.floor(duration.days());
            parts.push(days+" "+(days > 1 ? "days" : "day"));
        }
    
        if(duration.hours() >= 1) {
            const hours = Math.floor(duration.hours());
            parts.push(hours+" "+(hours > 1 ? "hrs" : "hr"));
        }
    
        if(duration.minutes() >= 1) {
            const minutes = Math.floor(duration.minutes());
            parts.push(minutes+" "+(minutes > 1 ? "mins" : "min"));
        }
    
        if(duration.seconds() >= 1) {
            const seconds = Math.floor(duration.seconds());
            parts.push(seconds+" "+(seconds > 1 ? "secs" : "sec"));
        }
    
        return parts.join(", ");
    }
};

export default utilities;
