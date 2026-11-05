"""Full pipeline. Stops before the golden eval because that needs your hand labels.
python run_all.py"""
import collect, tag, aggregate, make_golden
collect.main(); tag.main(); aggregate.main(); make_golden.main()
print("\nNext: label golden_set.csv by hand, then run golden_eval.py, "
      "make_mvp_golden.py and evidence_log.py")
