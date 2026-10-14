"""Great Expectations gate on the hourly demand mart. Exits non-zero if any check fails."""
import sys, duckdb
import great_expectations as gx
from great_expectations import expectations as gxe

# Load the dbt-built mart into a dataframe
df = duckdb.connect("transforms/energy.duckdb").sql("select * from mart_demand_hourly").df()

# Ephemeral GE context -> pandas datasource -> whole-dataframe batch
context = gx.get_context(mode="ephemeral")
asset = context.data_sources.add_pandas("energy").add_dataframe_asset("mart_demand_hourly")
batch = asset.add_batch_definition_whole_dataframe("whole").get_batch(
    batch_parameters={"dataframe": df})

# The expectations (what "good data" means for this project)
suite = context.suites.add(gx.ExpectationSuite(name="mart_quality"))
suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="demand_mw"))
suite.add_expectation(gxe.ExpectColumnValuesToBeBetween(column="demand_mw", min_value=500, max_value=8000))   # plausible ROI MW
suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="ts_hour"))
suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="ts_hour"))
suite.add_expectation(gxe.ExpectColumnValuesToBeBetween(column="temperature_2m", min_value=-20, max_value=45))
suite.add_expectation(gxe.ExpectColumnValuesToBeBetween(column="hour_of_day", min_value=0, max_value=23))
suite.add_expectation(gxe.ExpectTableRowCountToBeBetween(min_value=10000, max_value=100000))

# Run and gate
results = batch.validate(suite)
passed = sum(r.success for r in results.results)
print(f"\nExpectations passed: {passed}/{len(results.results)}")
for r in results.results:
    flag = "OK " if r.success else "FAIL"
    print(f"  [{flag}] {r.expectation_config.type}")
if not results.success:
    print("\n\u274c Data-quality gate FAILED")
    sys.exit(1)
print("\n\u2705 Data-quality gate PASSED")
