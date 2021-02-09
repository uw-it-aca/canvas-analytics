<template>
  <b-container fluid>
    <b-row class="mb-4">
      <b-col xs="12">
        <b-form class="d-flex flex-nowrap" inline>
          <label class="mr-2">Action</label>
          <b-form-select v-model="selectedAction" id="action-select" name="action-select">
            <b-form-select-option :value="'restart'">Restart selected (completed/failed)</b-form-select-option>
          </b-form-select>
          <b-button @click="handleAction()" variant="primary" size="md">
            Run
          </b-button>
          <b-form-checkbox v-show="selectedAction == 'restart'" v-model="ignoreStatus" class="ml-2" switch size="md">Include running and expired</b-form-checkbox>
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
            <b-form-select-option :value="5">5s</b-form-select-option>
            <b-form-select-option :value="10">10s</b-form-select-option>
            <b-form-select-option :value="15">15s</b-form-select-option>
            <b-form-select-option :value="20">20s</b-form-select-option>
            <b-form-select-option :value="25">25s</b-form-select-option>
            <b-form-select-option :value="30">30s</b-form-select-option>
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
          <td colspan="2">
            <date-range-picker
              ref="jobspicker"
              v-model="jobDateRange"
              :opens="'left'"
              :locale-data="dateLocale"
              :singleDatePicker="false"
              :showDropdowns="true"
              :showWeekNumbers="true"
              :ranges="false"
              :timePicker="true"
              :timePicker24Hour="true"
              :linkedCalendars="true"
              :autoApply="false"
            >
              <template v-slot:input="picker">
                <template v-if="picker.startDate && picker.endDate">
                  {{ picker.startDate | iso_date }} - {{ picker.endDate | iso_date}}
                </template>
                <template v-else>
                  <span class="picker-placeholder"><b-icon-calendar></b-icon-calendar>  All</span>
                </template>
              </template>

              <div slot="footer" slot-scope="data" class="picker-footer">
                <span>
                  {{data.rangeText}}
                </span>
                <span style="margin-left: auto">
                  <a @click="data.clickCancel" class="btn btn-light btn-sm">Cancel</a>
                  <a @click="clearJobDataPicker" class="btn btn-light btn-sm">Clear</a>
                  <a @click="data.clickApply" v-if="!data.in_selection" class="btn btn-primary btn-sm">Apply</a>
                </span>
              </div>
            </date-range-picker>
          </td>
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

        <template #cell(start)="row">
          {{row.item.start | iso_date}}
        </template>

        <template #cell(end)="row">
          {{row.item.end | iso_date}}
        </template>
    
        <template #cell(status)="row">
          {{row.item.status}}
          <b-badge href="#" class="error-badge" v-if="row.item.status == 'failed'" @click="showError(row.item)">
            error
          </b-badge>
        </template>
      </b-table>
    </b-row>
  </b-container>
</template>

<script>
import {mapState, mapMutations} from 'vuex';
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
              return 'table-' + item.status;
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
      ],
      selectedAction: 'restart',
      ignoreStatus: false,
      allSelected: false,
      jobStatusOptions: ['pending', 'running', 'completed', 'failed', 'expired']
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
    jobDateRange: {
      get () {
        return this.$store.state.jobDateRange;
      },
      set (value) {
        this.$store.commit('setJobDateRange', value);
      }
    },
  },
  methods: {
    handleAction: function() {
      if (this.selectedAction == 'restart') {
        let _this = this;
        let jobsToRestart = this.selectedJobs;
        if (!this.ignoreStatus) {
          jobsToRestart = jobsToRestart.filter(
            job => (job.status == "completed" ||  job.status == "failed"));
        }
        this.restartJobs(jobsToRestart).then(function() {
          jobsToRestart.forEach(function (job, index) {
            _this._setLocalPendingStatus(job);
          });
        });
      }
    },
    showError: function(job) {
       alert(job.message);
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
    clearJobDataPicker: function() {
      this.jobDateRange = {startDate: null, endDate: null};
      this.$refs.jobspicker.togglePicker(false);
    },
    _getColumnWidth: function(fieldKey) {
      if (fieldKey == "selected")
        return "25px";
      else if(fieldKey == "job_type")
        return "125%";
      else if(fieldKey == "context")
        return "150%";
      else if(fieldKey == "status")
        return "150%";
      else if (fieldKey == "start")
        return "150%";
      else if (fieldKey == "end")
        return "150%";
      else
        return "100%";
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

<style>
  .table-pending {
    color: #818182;
    background-color: #fefefe;
    border-color: #fdfdfe;
  }

  .table-running {
    color: #0c5460;
    background-color: #d1ecf1;
    border-color: #bee5eb;
  }

  .table-completed {
    color: #155724;
    background-color: #d4edda;
    border-color: #c3e6cb;
  }

  .table-failed {
    color: #721c24;
    background-color: #f8d7da;
    border-color: #f5c6cb;
  }

  .table-expired {
    color: #721c24;
    background-color: #f3f8d7;
    border-color: #eef5c6;
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

