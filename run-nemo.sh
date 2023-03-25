if [ $# -lt 6 ]; then
    echo "USAGE: bash $0 PROJECT_NAME MATRIX_NAME MATRIX_DIR MINIMIZATION_SCRIPTS_DIR WORKDIR OUT_DIR [CRITERIA_OPTION]"
    echo "if CRITERIA_OPTION is wTime, time will be included as a relative criterion."
    echo "if MATRIX_DIR is DEFAULT, then MINIMIZATION_SCRIPTS_DIR/mappings/PROJECT_NAME/matrix-MATRIX_NAME will be used."
    exit
fi

SCRIPT_DIR=$( cd $( dirname $0 ) && pwd )

PROJECT_NAME=$1
MATRIX=$2
MATRIX_DIR=$3
MINIMIZATION_SCRIPTS_DIR=$4
WORKDIR=$5
OUT_DIR=$6
mkdir -p ${OUT_DIR}
MODE_ARG=$7
if [ "${MODE_ARG}" == "wTime" ]; then
    echo "[$0] Running with criteria traces + violations + time"
    CONFIG_FILE_NAME=config.wTime.nemo-aux.json
    CPLEX_FILE_NAME=nemo-aux.wTime.cplex.lp
    SOLUTION_FILE_NAME=nemo-aux.wTime.sol.cplex
    out_file=${OUT_DIR}/multicriteriaWTime@${MATRIX}-minimized-test-suite.txt
    THIS_WORKDIR=${WORKDIR}/${PROJECT_NAME}@matrix-${MATRIX}-${MODE_ARG}
else
    echo "[$0] Running with criteria traces + violations"
    CONFIG_FILE_NAME=config.nemo-aux.json
    CPLEX_FILE_NAME=nemo-aux.cplex.lp
    SOLUTION_FILE_NAME=nemo-aux.sol.cplex
    out_file=${OUT_DIR}/multicriteria@${MATRIX}-minimized-test-suite.txt
    THIS_WORKDIR=${WORKDIR}/${PROJECT_NAME}@matrix-${MATRIX}
fi

if [ "${MATRIX_DIR}" == "DEFAULT" ]; then
    MATRIX_DIR=${MINIMIZATION_SCRIPTS_DIR}/mappings/${PROJECT_NAME}/matrix-${MATRIX}
fi

if [ ! -d ${MATRIX_DIR} ]; then
    echo "[$0] Matrix directory ${MATRIX_DIR} does not exist! Exiting..."
    exit
else
    echo "[$0] Using matrix directory ${MATRIX_DIR}..."
fi

function backup_old_results() {
    if [ -d ${THIS_WORKDIR} ]; then
        echo "****Moving old results"
        mv ${THIS_WORKDIR} ${THIS_WORKDIR}-`date +%Y-%m-%d-%H-%M-%S`
    fi
    mkdir -p ${THIS_WORKDIR}
}


function output_start_message() {
    local str="$1"
    local run_info="$2"
    local project="$3"
    if [ "${project}" == "" ]; then
        project_string=
    else
        project_string="${project}: "
    fi
    echo "${project_string}${str} started at `date +%Y-%m-%d-%H-%M-%S`" | tee -a ${run_info}
}

function output_end_message() {
    local str="$1"
    local run_info="$2"
    local project="$3"
    if [ "${project}" == "" ]; then
        project_string=
    else
        project_string="${project}: "
    fi
    echo "${project_string}${str} ended at `date +%Y-%m-%d-%H-%M-%S`" | tee -a ${run_info}
}

function setup_solver() {
    if [ ! -d ${SCRIPT_DIR}/PythonClient ]; then
        (
            cd ${SCRIPT_DIR}
            git clone git@github.com:NEOS-Server/PythonClient.git
        )
    fi
}

function main() {
    run_info=${THIS_WORKDIR}/run.info

    output_start_message "CONVERTING" ${run_info}
    python3 ${SCRIPT_DIR}/convert.py ${MATRIX_DIR}/all-tests.txt ${MATRIX_DIR}/mapping.csv ${MINIMIZATION_SCRIPTS_DIR}/violations-map/${PROJECT_NAME}-violations.csv ${MINIMIZATION_SCRIPTS_DIR}/test-time-files/${PROJECT_NAME}-times.csv ${THIS_WORKDIR}
    if [ "${res}" -eq 0 ]; then
        echo "$0: Conversion succeeded!"
    else
        echo "$0: Conversion failed, exiting..."
        exit
    fi
    cp ${SCRIPT_DIR}/config-files/${CONFIG_FILE_NAME} ${THIS_WORKDIR}
    output_end_message "CONVERTING" ${run_info}

    output_start_message "CREATING FORMULA FOR SOLVER" ${run_info}
    python2 ${SCRIPT_DIR}/formulator.py ${THIS_WORKDIR} ${CONFIG_FILE_NAME}
    bash ${SCRIPT_DIR}/create-xml.sh ${THIS_WORKDIR}/${CPLEX_FILE_NAME} ${THIS_WORKDIR}/job.xml
    output_end_message "CREATING FORMULA FOR SOLVER" ${run_info}

    output_start_message "RUNNING SOLVER" ${run_info}
    ( time python3 ${SCRIPT_DIR}/PythonClient/NeosClient.py ${THIS_WORKDIR}/job.xml ) &> ${THIS_WORKDIR}/${SOLUTION_FILE_NAME}
    output_end_message "RUNNING SOLVER" ${run_info}

    output_start_message "PROCESSING RESULTS" ${run_info}
    python2 ${SCRIPT_DIR}/generator.py ${THIS_WORKDIR} ${SOLUTION_FILE_NAME} ${out_file}
    # replacing the test aliases with the actual test names
    while read line; do
        id=$( echo "${line}" | cut -d, -f1 )
        tst=$( echo "${line}" | cut -d, -f2 )
        sed -i "s/^${id}$/${tst}/g" ${out_file}
    done < ${THIS_WORKDIR}/tests-ident-map.csv
    output_end_message "PROCESSING RESULTS" ${run_info}
}

backup_old_results
setup_solver
main
