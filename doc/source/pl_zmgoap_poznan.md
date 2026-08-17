# ZM GOAP Poznań (C-Trace)

Source for the former ZM GOAP system in the Poznań agglomeration (Poland).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pl_zmgoap_poznan
      args:
        service: zmgoappoznan
        ort: CZERNICE
        strasse: CZERNICE
        hausnummer: "4"
