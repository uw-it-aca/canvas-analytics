const datePickerMixin = {
    data: function() {
        return {
          dateLocale: {
            direction: 'ltr',
            separator: ' - ',
            weekLabel: 'Week',
            daysOfWeek: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
            monthNames: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            firstDay: 0
          },
        }
    },
}

export default datePickerMixin;
    