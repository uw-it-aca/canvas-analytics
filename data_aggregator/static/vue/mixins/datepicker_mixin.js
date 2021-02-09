const datePickerMixin = {
    data: function() {
        return {
          dateLocale: {
            direction: 'ltr',
            format: 'yyyy-mm-dd\'T\'HH:MM:ss',
            separator: ' - ',
            weekLabel: 'W',
            daysOfWeek: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
            monthNames: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            firstDay: 0
          },
        }
    },
}

export default datePickerMixin;
    