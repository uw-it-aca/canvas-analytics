import axios from 'axios';

const dataMixin = {
    methods: {
        getJobs: async function(filters) {
            // cancel previous ajax if exists
            if (this.$store.state.getJobsAjaxRequest != null) {
                this.$store.state.getJobsAjaxRequest.cancel(); 
            }
            if (!filters) {
                filters = {};
            }

            // set the cancel token before the request
            this.$store.commit('setGetJobsAjaxRequest',
                               axios.CancelToken.source()); 
            const csrfToken = this.$store.state.csrfToken;
            const axiosConfig = {
              headers: {
                'Content-Type': 'application/json;charset=UTF-8',
                'Access-Control-Allow-Origin': '*',
                'X-CSRFToken': csrfToken,
              },
              cancelToken: this.$store.state.getJobsAjaxRequest.token,
            };
            
            return axios.post(
                `api/internal/jobs/`,
                filters,
                axiosConfig
            );
        },
        getJobsChartData: async function(filters) {
            if (!filters) {
                filters = {};
            }

            const csrfToken = this.$store.state.csrfToken;
            const axiosConfig = {
              headers: {
                'Content-Type': 'application/json;charset=UTF-8',
                'Access-Control-Allow-Origin': '*',
                'X-CSRFToken': csrfToken,
              },
            };
            
            return axios.post(
                `api/internal/jobs-chart-data/`,
                filters,
                axiosConfig
            );
        },
        restartJobs: async function(jobs) {
            const csrfToken = this.$store.state.csrfToken;
            const axiosConfig = {
            headers: {
                'Content-Type': 'application/json;charset=UTF-8',
                'Access-Control-Allow-Origin': '*',
                'X-CSRFToken': csrfToken
            }
            };
            return axios.post(
                `api/internal/jobs/restart/`,
                {"job_ids": jobs.map(job => job.id)},
                axiosConfig
            );
        },
    },
};

export default dataMixin;
    