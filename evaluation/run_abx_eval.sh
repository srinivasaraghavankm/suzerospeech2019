#!/bin/bash

# The first argument is the input hknpz-format .npz file to be evaluated inside the docker image.
#
# Author: Ewald van der Westhuizen
# Date: Feb 2019
#

innpzfn=$1

baseline_zipfn="baseline_submission.zip"
#baseline_zip_src="/home/ewaldvdw/projects/docker/zs2019_baseline_exported_filesystem/home/zs2019/baseline/${baseline_zipfn}"
baseline_zip_src="/media/data1/suzero/docker/zs2019_home/baseline/${baseline_zipfn}"
docker_homedir="/media/data1/suzero/docker/zs2019_home"

tmpdir="$(dirname ${innpzfn})"
tmpname="$(basename ${tmpdir})"

echo "Running $0 on feature file ${innpzfn}"

#mkdir -p "${tmpdir}"

# Convert the .npz file to text based format that submission/evaluation expects.
python /home/suzero/suzerospeech2019/features/hknpz_to_text.py "${innpzfn}" "${tmpdir}/textfeatures"

# Create the submission zip file containing the features.
#  First, copy the baseline_submission.zip to "hack" it with our features.
echo "Copying baseline_submission.zip ..."
cp "${baseline_zip_src}" "${tmpdir}/"
echo "Unzipping baseline_submission.zip ..."
unzip -d "${tmpdir}/unzipped" "${tmpdir}/${baseline_zipfn}" > /dev/null
rm "${tmpdir}/unzipped/english/auxiliary_embedding1/"*
rm "${tmpdir}/unzipped/english/auxiliary_embedding1/.txt"

echo "Copying text format feature files ..."
cp "${tmpdir}/textfeatures/"*.txt "${tmpdir}/unzipped/english/auxiliary_embedding1/"

cd "${tmpdir}/unzipped"
zip -r "${tmpdir}/${tmpname}.zip" "./" > /dev/null
cd /home/suzero

echo "Cleaning temporary files..."
rm "${tmpdir}/${baseline_zipfn}"
rm -rf "${tmpdir}/unzipped/"
rm -rf "${tmpdir}/textfeatures/"

echo "Copying submission zip to docker home dir ..."
#echo "mkdir -p ${docker_homedir}/${tmpname}/"
mkdir -m 775 -p "${docker_homedir}/evaluations/${tmpname}/"
mkdir -m 775 -p "${docker_homedir}/evaluations/${tmpname}/working/"
chown suzero:docker "${docker_homedir}/evaluations/${tmpname}/"
chown suzero:docker "${docker_homedir}/evaluations/${tmpname}/working/"
#echo "copy to tmp dir ..."
#echo "cp ${tmpdir}/${tmpname}.zip ${docker_homedir}/${tmpname}/"
cp "${tmpdir}/${tmpname}.zip" "${docker_homedir}/evaluations/${tmpname}/"

# The submission zip file name as it will be referenced from within the docker container.
submissionzipfn="/home/zs2019/evaluations/${tmpname}/${tmpname}.zip"
echo "Submission zip-file name: ${submissionzipfn}"

echo "Executing docker ..."
# Execute the evaluation process in a docker container.
docker run -t --rm -v /media/data1/suzero/docker/shared:/shared -v /media/data1/suzero/docker/zs2019_home:/home/zs2019 zeroresource/zs2019:latest bash /home/zs2019/suzero_evaluate.sh "${submissionzipfn}" auxiliary_embedding1 dtw_cosine
