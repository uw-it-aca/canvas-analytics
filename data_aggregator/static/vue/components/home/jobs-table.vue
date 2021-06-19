<template>
  <b-container fluid>
    <b-row class="mb-4">
      <b-col xs="12">
        <b-form class="d-flex flex-nowrap" inline>
          <label class="mr-2">Action</label>
          <b-form-select v-model="selectedAction" id="action-select" name="action-select">
            <b-form-select-option :value="'restart'">Restart selected</b-form-select-option>
            <b-form-select-option :value="'clear'">Clear status of selected</b-form-select-option>
          </b-form-select>
          <b-button @click="handleAction()" variant="primary" size="md">
            Run
          </b-button>
        </b-form>
      </b-col>
    </b-row>
    <b-row>
      <b-col xs="12" md="5">
        <b-pagination
          v-if="totalJobs > 0"
          v-model="currPage"
          :total-rows="totalJobs"
          :per-page="perPage"
          aria-controls="jobs-table"
          size="sm"
          limit="7"
          first-number
          last-number
          >
        </b-pagination>
      </b-col>
      <b-col xs="12" md="7">
        <b-form class="d-flex flex-nowrap" inline>
          <label class="ml-2 mr-2">Auto Refresh</label>
          <b-form-select v-model="refreshTime" id="refresh-select" name="refresh-select">
            <b-form-select-option :value="30">30s</b-form-select-option>
            <b-form-select-option :value="60">60s</b-form-select-option>
            <b-form-select-option :value="99999">Off</b-form-select-option>
          </b-form-select>
          <label class="ml-2 mr-2">Page Size</label>
          <b-form-select v-model="perPage" id="page-size" name="page-size">
            <b-form-select-option :value="100">100</b-form-select-option>
            <b-form-select-option :value="250">250</b-form-select-option>
            <b-form-select-option :value="500">500</b-form-select-option>
            <b-form-select-option :value="1000">1000</b-form-select-option>
          </b-form-select>
        </b-form>
      </b-col>
    </b-row>
    <b-row>
      <b-table id="jobs-table"
        :items="jobs"
        :fields="fields"
        :per-page="0"
        :busy="isLoading"
        :current-page="currPage"
        :primary-key="'id'"
        :no-local-sorting="true"
        :sort-by.sync="sortBy"
        :sort-desc.sync="sortDesc"
        stacked="sm"
        fixed
        bordered
        small
        >

        <template #table-busy>
          <div class="text-center text-danger my-2">
            <b-spinner class="align-middle"></b-spinner>
            <strong>Loading...</strong>
          </div>
        </template>

        <template #table-colgroup="scope">
          <col
            v-for="field in scope.fields"
            :key="field.key"
            :style="{ width: _getColumnWidth(field.key) }"
          >
        </template>

        <template slot="thead-top" slot-scope="{ fields }">
          <td></td>
          <td>
            <multiselect
              id="jobTypes"
              name="jobtype"
              v-model="jobType"
              :multiple="true"
              :options="jobTypes"
              :searchable="false"
              :close-on-select="false"
              :show-labels="false"
              placeholder="All">
            </multiselect>
          </td>
          <td></td>
          <td>
            <multiselect
              id="jobstatuses"
              name="jobstatus"
              v-model="jobStatus"
              :multiple="true"
              :options="jobStatusOptions"
              :searchable="false"
              :close-on-select="false"
              :show-labels="false"
              placeholder="All">
            </multiselect>
          </td>
          <td></td>
          <td></td>
          <td></td>
        </template>

        <template #head(selected)="">
          <input type="checkbox" id="checkbox" @click="selectAll" v-model="allSelected">
        </template>

        <template #cell(selected)="row">
          <input type="checkbox" id="checkbox" @click="select" v-model="row.item.selected">
        </template>

        <template #cell(context)="row">
          <ul class="list-unstyled m-0">
            <li v-for="(value, name) in row.item.context" :key="value">
              {{name}} : {{ value }}
            </li>
          </ul>
        </template>

        <template #cell(status)="row">
          {{row.item.status}}
          <span v-if="row.item.status == 'completed'">
            ({{row.item | execution_time}})
          </span>
          <span v-if="row.item.status == 'running'" >
            <time-difference-widget :start-time="row.item.start"></time-difference-widget>
          </span>
          <b-badge href="#" class="error-badge" v-if="row.item.status == 'failed'" @click="showError(row.item)">
            error
          </b-badge>
        </template>

        <template #cell(start)="row">
          {{row.item.start | iso_date}}
        </template>

        <template #cell(end)="row">
          {{row.item.end | iso_date}}
        </template>

        <template #cell(created)="row">
          {{row.item.created | iso_date}}
        </template>
      </b-table>
    </b-row>
  </b-container>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
import utilities from "../../../js/utilities.js";
import dataMixin from '../../mixins/data_mixin';
import utilitiesMixin from '../../mixins/utilities_mixin';
import datePickerMixin from '../../mixins/datepicker_mixin';

export default {
  name: 'jobs-table',
  mixins: [dataMixin, utilitiesMixin, datePickerMixin],
  props: ['selectedJobs'],
  data: function() {
    return {
      fields: [
        { key: 'selected',
          label: '',
          sortable: false,
        },
        { key: 'job_type',
          label: 'Job Type',
          sortable: true,
        },
        { key: 'context',
          label: 'Job Context',
          sortable: false,
        },
        { key: 'status',
          label: 'Job Status',
          tdClass: (value, key, item) => {
              return item.status;
          },
          sortable: true,
        },
        { key: 'start',
          label: 'Job Start',
          sortable: true,
        },
        { key: 'end',
          label: 'Job End',
          sortable: true,
        },
        { key: 'created',
          label: 'Job Created',
          sortable: true,
        },
      ],
      selectedAction: 'restart',
      allSelected: false,
      jobStatusOptions: ['pending', 'claimed', 'running', 'completed',
                         'failed', 'expired']
    }
  },
  computed: {
    ...mapState({
      jobs: (state) => state.jobs,
      jobTypes: (state) => state.jobTypes,
      isLoading: (state) => state.isLoading,
      totalJobs: (state) => state.totalJobs,
    }),
    refreshTime: {
      get () {
        return this.$store.state.refreshTime;
      },
      set (value) {
        this.$store.commit('setRefreshTime', value);
      }
    },
    sortBy: {
      get () {
        return this.$store.state.sortBy;
      },
      set (value) {
        this.$store.commit('setSortBy', value);
      }
    },
    sortDesc: {
      get () {
        return this.$store.state.sortDesc;
      },
      set (value) {
        this.$store.commit('setSortDesc', value);
      }
    },
    jobStatus: {
      get () {
        return this.$store.state.jobStatus;
      },
      set (value) {
        this.$store.commit('setJobStatus', value);
      }
    },
    jobType: {
      get () {
        return this.$store.state.jobType;
      },
      set (value) {
        this.$store.commit('setJobType', value);
      }
    },
    perPage: {
      get () {
        return this.$store.state.perPage;
      },
      set (value) {
        this.$store.commit('setPerPage', value);
      }
    },
    currPage: {
      get () {
        return this.$store.state.currPage;
      },
      set (value) {
        this.$store.commit('setCurrPage', value);
      }
    },
  },
  methods: {
    handleAction: function() {
      if (this.selectedAction == 'restart') {
        let _this = this;
        let jobsToRestart = this.selectedJobs;
        if (jobsToRestart.length == 0) {
          this.showNoSelectedJobsWarning();
        } else {
          this.showActionWarning(jobsToRestart, this.selectedAction)
          .then(choice => {
            if (choice) {
              _this.restartJobs(jobsToRestart).then(function(choice) {
                jobsToRestart.forEach(function (job, index) {
                  _this._setLocalPendingStatus(job);
                });
              });
            }
          });
        }
      } else if (this.selectedAction == 'clear') {
        let _this = this;
        let jobsToClear = this.selectedJobs;
        if (jobsToClear.length == 0) {
          this.showNoSelectedJobsWarning();
        } else {
          this.showActionWarning(jobsToClear, this.selectedAction)
          .then(choice => {
            if (choice) {
              _this.clearJobs(jobsToClear).then(function() {
                jobsToClear.forEach(function (job, index) {
                  _this._setLocalPendingStatus(job);
                });
              });
            }
          });
        }
      }
    },
    showError: function(job) {
        this.$bvModal.msgBoxOk(
          job.message,
          {
            title: 'Error Log',
            size: 'xl',
            buttonSize: 'md',
            okVariant: 'secondary',
            okTitle: 'Dismiss',
            footerClass: 'p-2',
            hideHeaderClose: false,
            centered: true
          })
    },
    showNoSelectedJobsWarning: function() {
        this.$bvModal.msgBoxOk(
          'Select jobs to perform an action',
          {
            title: 'No jobs selected',
            size: 'sm',
            buttonSize: 'md',
            okVariant: 'secondary',
            okTitle: 'Dismiss',
            footerClass: 'p-2',
            hideHeaderClose: false,
            centered: true
          })
    },
    showActionWarning: function(jobs, action) {
      // create warning message
      const h = this.$createElement;
      let cntByStatus = utilities.countByProperty(jobs, "status");
      let listItems = [];
      for (const [key, value] of Object.entries(cntByStatus)) {
        listItems.push(
          h('div', {class: [key]}, key + ": " + value)
        );
      }
      const warningVNode = h('div', [
        h('p', {class: ['text-left']}, [
          'Please confirm that you want to ',
          h('b', action),
          ' the following jobs:',
        ]),
        listItems
      ]);

      return this.$bvModal.msgBoxConfirm(
        warningVNode,
        {
          title: 'Please Confirm',
          size: 'sm',
          buttonSize: 'md',
          okVariant: 'danger',
          okTitle: 'Yes',
          cancelVariant: 'secondary',
          cancelTitle: 'No',
          footerClass: 'p-2',
          hideHeaderClose: false,
          centered: true
      })
    },
    selectAll: function() {
      let _this = this;
      this.jobs.forEach(function (job, index) {
        job.selected = !_this.allSelected;
      });
    },
    select: function() {
      this.allSelected = false;
    },
    _getColumnWidth: function(fieldKey) {
      if (fieldKey == "selected")
        return "25px";
      else if(fieldKey == "job_type")
        return "15%";
      else if(fieldKey == "context")
        return "25%";
      else if(fieldKey == "status")
        return "15%";
      else if (fieldKey == "start")
        return "15%";
      else if (fieldKey == "end")
        return "15%";
      else
        return "15%";
    },
    _setLocalPendingStatus: function(job) {
      job.pid = "";
      job.start = "";
      job.end = "";
      job.message = "";
      job.status = "pending";
    },
    ...mapMutations([
      'addVarToState',
    ]),
  },
};
</script>

<style lang="scss">
  @import "../../../css/data_aggregator/variables.scss";

  .pending {
      color: #818182;
      background-color: map-get($theme-colors, "pending-bg");
  }

  .claimed {
      color: #7237b5;
      background-color: map-get($theme-colors, "claimed-bg");
  }

  .running {
    color: #0c5460;
    background-color: map-get($theme-colors, "running-bg");
  }

  .completed {
    color: #155724;
    background-color: map-get($theme-colors, "completed-bg");
  }

  .failed {
    color: #721c24;
    background-color: map-get($theme-colors, "failed-bg");
  }

  .expired {
    color: #721c24;
    background-color: map-get($theme-colors, "expired-bg");
  }

  .error-badge {
    color: #721c24;
    background-color:  #f5c6cb;
    border-color: #f8d7da;
  }

  .reportrange-text {
    min-height: 40px;
    min-width: 150px;
    border: 1px solid #e8e8e8 !important;
  }

  .picker-placeholder {
    color: #afafaf;
  }

  .picker-footer {
    padding: 0.5rem;
    color: black;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
</style>

