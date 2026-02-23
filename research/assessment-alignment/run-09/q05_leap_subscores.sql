WITH raw_data AS (
  SELECT * FROM `fls-data-warehouse.leap.399001LEAPData24_25_full`
  UNION ALL
  SELECT * FROM `fls-data-warehouse.leap.399002LEAPData24_25_full`
  UNION ALL
  SELECT * FROM `fls-data-warehouse.leap.399004LEAPData24_25_full`
)
SELECT
  TRIM(LASID) as LASID,
  SAFE_CAST(Grade AS INT64) as grade,
  SAFE_CAST(ELAScaleScore AS INT64) as ela_ss,
  SAFE_CAST(MathScaleScore AS INT64) as math_ss,
  SAFE_CAST(ScienceScaleScore AS INT64) as sci_ss,
  SAFE_CAST(SocialScaleScore AS INT64) as ss_ss,
  -- ELA subscores (universal across grades)
  ReadingInformationalText as ela_ri,
  ReadingLiteraryText as ela_rl,
  ReadingVocabulary as ela_vocab,
  ELAReadingPerformance as ela_read_perf,
  ELAWritingPerformance as ela_write_perf,
  -- Science subscores (universal across grades)
  Investigate as sci_investigate,
  Evaluate as sci_evaluate,
  ReasonScientifically as sci_reason,
  -- Math subscores (grade-specific; take all that exist)
  MajorContent as math_major,
  AdditionalSupportingContent as math_additional,
  MathematicalReasoningModeling as math_reasoning,
  -- Grade-specific Math domains
  FractionsasNumbersEquivalence as math_fractions_equiv,
  ProductsQuotientsSolveMultiplicationDivisionProblems as math_mult_div,
  SolveProblemswithAnyOperation as math_any_op,
  SolveTimeAreaMeasurementEstimationProblems as math_measurement,
  MultiplicativeComparisonPlaceValue as math_place_value,
  CompareSolveProblemswithFractions as math_compare_fractions,
  SolveFractionProblems as math_fraction_problems,
  SolveMultistepProblems as math_multistep,
  InterpretFractionsPlaceValueScaling as math_interpret_fractions,
  RecognizeRepresentDetermineVolumeMultiplyDivideWholeNumbers as math_volume_whole,
  OperationswithDecimalsReadWriteCompareDecimals as math_decimals,
  RatioRate as math_ratio_rate,
  ExpressionsInequalitiesEquations as math_expr_ineq,
  RationalNumbersMultiplyDivideFractions as math_rational,
  AnalyzeProportionalRelationshipsSolveProblems as math_proportional,
  OperationswithRationalNumbers as math_rational_ops,
  ProportionalRelationshipsLinearEquationsFunctions as math_linear,
  RadicalsIntegerExponentsScientificNotation as math_radicals,
  SolvingLinearEquationsSystemsofLinearEquations as math_solving_linear,
  CongruenceSimilarityPythagoreanTheorem as math_congruence,
  -- Social Studies subscores (grade-specific topics)
  EstablishingContext as ss_establishing_context,
  ExaminingSourcesandExpressingClaims as ss_examining_sources,
  FoundationsPapersandPlacesoftheUnitedStatesofAmerica as ss_foundations,
  AGrowingandChangingNation as ss_growing_nation,
  IndustryInnovationandaMorePerfectUnion as ss_industry,
  -- Additional SS topics
  AmericanRevolution as ss_american_rev,
  TheCivilWarandReconstruction as ss_civil_war,
  TheFirstPresidentsthroughtheEraofGoodFeelings as ss_first_presidents
FROM raw_data
