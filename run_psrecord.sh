
mkdir -p psrecord-output/
TIMESTAMP=$(date +"%Y-%m-%dT%H:%M:%S%z")

# detect macOS (Darwin) to disable --include-io there
if [[ "$(uname -s)" == "Darwin" ]]; then
  IO_FLAG=""
else
  IO_FLAG="--include-io"
fi

psrecord \
  $IO_FLAG \
  --include-children \
  --log psrecord-output/${TIMESTAMP}.txt \
  --plot psrecord-output/${TIMESTAMP}.png \
  "streamlit run src/fractal_feature_explorer/main.py"

