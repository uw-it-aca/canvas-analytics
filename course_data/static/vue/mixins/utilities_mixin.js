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
}

export default utilitiesMixin;
    