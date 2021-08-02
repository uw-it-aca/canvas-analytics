import { Vue } from './admin_base.js';
import Vuex from 'vuex';

// custom components
import AdminMetadata from '../components/admin/metadata.vue';

Vue.component('admin-metadata', AdminMetadata);

// stores
import admin_store from '../vuex/store/admin_store.js';

// mixins
import dataMixin from '../mixins/data_mixin';

const store = new Vuex.Store({
  state: {
    // data set on load
    pageTitle: "Canvas Analytics: Metadata",
    metadataFiles: [],
    terms: JSON.parse(document.getElementById('terms').innerHTML),
    csrfToken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
  },
  mutations: {
    setMetadataFiles(state, value) {
      state.metadataFiles = value;
    },
  },
  modules: {
    'admin_store': admin_store
  }
});

// initialize root component
import { mapState } from 'vuex';

new Vue({
  el: '#vue_root',
  store: store,
  mixins: [dataMixin],
  data: function () {
    return {};
  },
  created: function () {
    document.getElementById('vue_root').hidden = false;
    this.refreshMetadata();
  },
  computed: {
    ...mapState({
    }),
  },
  methods: {
    refreshMetadata: function () {
      let _this = this;
      let promise = this.getMetadataFilesList()
        .then(response => {
          if (response.data) {
            // we need to reset all selected ids on every refresh
            _this.$store.commit('setMetadataFiles',
              response.data["metadata_files"]);
          }
        });
      return promise;
    },
  },
  beforeDestroy() {
    clearInterval(this.refreshMetadata);
  },
});