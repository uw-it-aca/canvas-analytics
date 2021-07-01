import Vue from 'vue';
import Vuex from 'vuex';

import { BootstrapVue, BootstrapVueIcons } from 'bootstrap-vue'
import VueGoogleCharts from 'vue-google-charts'

// Import Bootstrap an BootstrapVue CSS files (order is important)
import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap-vue/dist/bootstrap-vue.css';

import '../css/data_aggregator/custom.scss';
import '../css/data_aggregator/variables.scss';

// Make BootstrapVue available throughout project
Vue.use(BootstrapVue);
Vue.use(BootstrapVueIcons);

// Vue Google Charts
Vue.use(VueGoogleCharts);

// vuex
Vue.use(Vuex);

Vue.config.devtools = true;

export {Vue};
