const utilitiesMixin = {
    filters: {
        date: function(value) {
          var options = {
              year: "numeric",
              month: "2-digit",
              day: "numeric"
          };
          return value ? new Date(value).toLocaleString('en-US', options) : '';
        },
        iso_date: function(value) {
            let iso_date = '';
            if(value) {
              iso_date = new Date(new Date(value).toString().split('GMT')[0]+' UTC')
                                  .toISOString().split('.')[0]+'Z';
            }
            return iso_date;
        }
    },
}

export default utilitiesMixin;
    