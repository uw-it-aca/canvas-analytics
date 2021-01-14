const utilitiesMixin = {
    methods: {
        getStatus: function(job) {
            if (!job.pid && !job.start && !job.end && !job.message)
              return "pending";
            else if (job.pid && job.start && !job.end && !job.message)
              return "running";
            else if (job.pid && job.start && job.end && !job.message)
              return "completed";
            else if (job.message)
              return "failed";
        },
    },
    filters: {
        date: function(value) {
          var options = {
              year: "numeric",
              month: "2-digit",
              day: "numeric"
          };
          return value ? new Date(value).toLocaleString('en-US', options) : '';
        }
    },
}

export default utilitiesMixin;
    