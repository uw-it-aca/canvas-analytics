import axios from 'axios';

const dataMixin = {
    methods: {
        getJobs: async function(filters) {
            this.$store.state.isLoading = true;
            if (!filters) {
                filters = {};
            }
            const csrfToken = this.$store.state.csrfToken;
            const axiosConfig = {
            headers: {
                'Content-Type': 'application/json;charset=UTF-8',
                'Access-Control-Allow-Origin': '*',
                'X-CSRFToken': csrfToken
            }
            };
            return axios.post(
                `api/filterjobs/`,
                filters,
                axiosConfig
            );
        },
    },
}

export default dataMixin;
    