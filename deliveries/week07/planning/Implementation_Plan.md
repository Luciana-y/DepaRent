# Implementation Plan – DepaRent

## 1. Purpose

This implementation plan defines the prioritized development roadmap for **DepaRent – Plataforma inteligente para propietarios de departamentos en alquiler** from Week 7 through Week 15.

The plan is aligned with the official milestones of the Data Product Development course and organizes the work required to transform the current analytical definition into a functional, evaluated, reproducible, and demonstrable Data Product.

The implementation follows four progressive stages:

**Definition and consolidation → Functional prototype → Refinement and evaluation → Final product**

---

## 2. Prioritization Criteria

Tasks are prioritized according to four criteria:

1. **Technical dependency:** components required by later stages are implemented first.
2. **Product value:** priority is given to functionalities directly related to the two main user requirements.
3. **Technical risk:** analytical components requiring validation are addressed before final interface integration.
4. **Course milestones:** implementation is organized around the official Week 7, Week 10, Week 12, and Week 15 submissions.

Priority levels:

- **P0 – Critical:** required for the next official milestone or blocks other components.
- **P1 – High:** core functionality of the Data Product.
- **P2 – Medium:** refinement, usability, validation, or supporting functionality.

---

## 3. Product Components to Implement

DepaRent is organized around two main product requirements.

### Requirement 1 – Analyze and Value the Property

The platform will provide the owner with an integrated analysis containing:

- competitive property profile;
- comparable properties;
- accessibility profile;
- expected rental price;
- district market trend.

Main analytical components:

- K-Means clustering for competitive segmentation;
- nearest-neighbor or similarity-based comparable retrieval;
- spatial accessibility indicators using ATU data;
- HistGradientBoosting for expected rental price prediction;
- SARIMA for district-level rental trend forecasting.

### Requirement 2 – Recommend a Publication Strategy

Using the analytical results from Requirement 1, the platform will provide:

- competitive price scenario;
- balanced price scenario;
- higher-rent scenario;
- improvement simulation;
- support for selecting the final publication price.

The recommendation layer will reuse the analytical outputs rather than introduce an additional independent Machine Learning model.

---

## 4. Implementation Roadmap

| Period | Official milestone | Priority | Main implementation activities | Expected result | Main responsibility |
|---|---|---:|---|---|---|
| **Week 7 – Sep. 23** | **Delivery 1 – Integrated Project Definition** | P0 | Consolidate problem definition, users, requirements, Data Product Canvas, EDA, model selection, architecture, workflows, wireframes, implementation plan and responsibilities. Organize processed datasets and preliminary code in the repository. | Complete and internally consistent first-phase project definition. | Entire team |
| **Week 8** | **No official project deliverable** | P0 | Review instructor feedback from Delivery 1. Refine scope, requirements and architecture. Resolve inconsistencies in documentation and models. Stabilize the processed datasets and define final input/output schemas for analytical components. | Stable technical specification for implementation. | Entire team |
| **Week 9** | Internal implementation sprint | P1 | Consolidate the preprocessing pipeline. Implement the final competitive segmentation and property-comparable retrieval. Stabilize ATU accessibility features. Define reusable functions for inference. | Reproducible preprocessing pipeline and operational competitive/accessibility modules. | Adrian + Armando + Breysi |
| **Week 10 – Oct. 14** | **Functional Prototype** | P0 | Integrate the principal product workflow. Finalize the first deployable rental-price model. Connect property input with preprocessing and analytical inference. Implement an initial web interface and dashboard using real or representative project data. | Functional prototype demonstrating the main DepaRent workflow. | Entire team |
| **Week 11** | Internal refinement sprint | P1 | Improve predictive model validation and parameter tuning. Implement district forecasting. Integrate clustering, accessibility, price prediction and district trend into a unified analytical response. Begin recommendation-engine implementation. | Integrated analytical pipeline feeding the product interface. | Breysi + Armando |
| **Week 12 – Oct. 28** | **Refined Prototype, Evaluation and Case Studies** | P0 | Complete the recommendation engine and improvement simulator. Refine frontend and dashboard. Execute baseline comparisons, model validation, error analysis and functional testing. Prepare at least one realistic owner use case. | Refined prototype with evaluation evidence and realistic case study. | Entire team |
| **Week 13** | Internal integration sprint | P1 | Correct technical and usability issues detected in Week 12. Improve frontend–backend integration. Stabilize inference functions, error handling and application states. Update architecture and documentation when necessary. | Stable integrated product candidate. | Luciana + Armando + Breysi |
| **Week 14** | Final validation sprint | P0 | Conduct end-to-end tests, reproducibility checks and final usability review. Freeze final processed data and model artifacts. Prepare final diagrams, requirements, Data Product Canvas, README, project page and demonstration flow. | Final release candidate ready for presentation. | Entire team |
| **Week 15 – Nov. 18** | **Delivery 2 + Final Presentation** | P0 | Finalize deployment, repository, documentation, evaluation results, case studies, final report, presentation and demo video. Verify that the product can be reproduced and executed following repository instructions. | Complete, reproducible and demonstrable Data Product. | Entire team |

---

## 5. Detailed Implementation by Component

| Component | Implementation target | Priority | Dependency | Completion target |
|---|---|---:|---|---|
| Data preprocessing pipeline | Reproducible cleaning, transformation and feature generation | P0 | Raw datasets | Week 9 |
| Competitive profile | Final K-Means segmentation | P1 | Processed property data | Week 9 |
| Comparable properties | Similar properties within relevant competitive context | P1 | Competitive profile | Week 9–10 |
| Accessibility profile | ATU spatial indicators using property coordinates | P1 | ATU + geolocation | Week 9 |
| Expected rental price | Validated HistGradientBoosting inference pipeline | P0 | Processed property features | Week 10 |
| District trend | SARIMA-based district rental trend | P1 | BCRP time series | Week 11 |
| Integrated analytical response | Combine competitive, accessibility, prediction and trend results | P0 | Analytical modules | Week 11 |
| Publication scenarios | Competitive, balanced and higher-rent scenarios | P1 | Expected price + comparables + trend | Week 12 |
| Improvement simulator | Counterfactual re-evaluation of modifiable property attributes | P1 | Price prediction model | Week 12 |
| Owner dashboard | Integrated visualization of analytical results | P0 | Analytical outputs | Week 10–12 |
| Property management | Register and manage one or multiple properties | P1 | Application backend | Week 10–13 |
| Public property view | Display published property information | P2 | Application/frontend | Week 13–14 |
| Product testing | Functional, analytical and usability validation | P0 | Integrated prototype | Week 12–14 |
| Deployment and reproducibility | Executable product and complete setup documentation | P0 | Final integrated system | Week 14–15 |

---

## 6. Main Technical Dependencies

The implementation follows the dependency chain below:

**Raw data**

→ **Preprocessing and feature engineering**

→ **Processed datasets**

→ **Competitive profile / Accessibility / Price Prediction / District Trend**

→ **Integrated property analysis**

→ **Publication recommendation engine**

→ **Improvement simulator**

→ **Owner dashboard**

→ **Publication decision**

This dependency structure determines the development order.

The recommendation engine cannot be finalized until the main analytical components provide stable outputs.

Similarly, the improvement simulator depends directly on the validated price-prediction pipeline because it recalculates the expected price under hypothetical modifications to property attributes.

---

## 7. Milestone Acceptance Criteria

### Week 7 – Delivery 1

Delivery 1 will be considered complete when:

- the problem and value proposition are clearly defined;
- target users and stakeholders are identified;
- requirements are consolidated;
- the processed datasets and data dictionary are available;
- EDA findings and limitations are documented;
- the analytical approach and baselines are specified;
- the initial architecture and workflow are documented;
- wireframes or low-fidelity interface representations are available;
- the implementation plan and team responsibilities extend through Week 15;
- the repository structure is understandable and reproducible.

---

### Week 10 – Functional Prototype

The functional prototype should allow a representative end-to-end workflow:

**Property input  
→ preprocessing  
→ analytical processing  
→ presentation of results**

At minimum, the prototype should demonstrate:

- property registration or input;
- use of real or representative processed data;
- execution of the principal analytical component;
- visualization of the main results;
- a functional interface connecting the user workflow with the analytical pipeline.

Final styling and all secondary functionalities are not required at this stage.

---

### Week 12 – Refined Prototype

The refined prototype should include:

- integration of the major analytical components;
- improved interface consistency;
- expected rental-price prediction;
- competitive and accessibility context;
- district trend where available;
- publication scenarios;
- improvement simulation;
- validation metrics;
- comparison against baselines;
- error or limitation analysis;
- functional testing evidence;
- at least one realistic case study involving a target owner.

---

### Week 15 – Final Product

The final version must provide:

- a complete and functional DepaRent application;
- reproducible source code;
- final processed data or legal acquisition instructions;
- preprocessing, training, inference and evaluation scripts;
- required model artifacts;
- final architecture and workflow diagrams;
- final requirements and Data Product Canvas;
- evaluation results and baseline comparisons;
- realistic case studies;
- complete README and execution instructions;
- deployed product when technically feasible;
- final report;
- final presentation;
- 5–7 minute demonstration video;
- team contribution statement;
- final project-development reflection.

---

## 8. Validation Strategy

Implementation will not be considered complete solely because a model or interface executes.

Each analytical component must provide evidence of validation.

### Competitive Profile

Validation should consider:

- cluster interpretability;
- cluster stability;
- silhouette score;
- usefulness of retrieved comparable properties.

### Expected Rental Price

Validation should include:

- MAE;
- RMSE;
- MAPE;
- R²;
- comparison with baseline models;
- analysis of prediction errors.

### District Trend

Validation should use temporal separation between training and validation periods whenever possible and compare SARIMA with an appropriate temporal baseline.

### Recommendation Engine

Validation should verify:

- logical consistency between predicted price, comparable market values and district trend;
- consistency between competitive, balanced and higher-rent scenarios;
- absence of impossible or contradictory recommendations.

### Improvement Simulator

Results must be presented as estimated associations derived from the predictive model and not as guaranteed causal effects of a renovation or improvement.

### Product

Product validation should include:

- end-to-end workflow testing;
- error handling;
- consistency between analytical output and displayed information;
- basic usability observations;
- reproducibility from repository instructions.

---

## 9. Risk Management

| Risk | Potential impact | Mitigation |
|---|---|---|
| Incomplete or ambiguous property attributes | Reduced prediction or segmentation quality | Preserve missingness indicators and disclose uncertainty |
| Asking prices differ from actual transaction prices | Predictions represent market asking-price behavior rather than final contracts | Clearly communicate the interpretation of the target variable |
| Limited BCRP district coverage | District trend unavailable or less specific for some properties | Use available reference information and disclose fallback cases |
| ATU data may not reflect the most recent transport infrastructure | Accessibility indicators may omit newer infrastructure | Document the temporal limitation of the source |
| Weak clustering separation | Competitive segments may not represent naturally distinct market groups | Validate interpretability and complement clustering with similarity-based comparables |
| Model integration delays | Prototype may not expose all analytical functionality | Prioritize the principal owner workflow and integrate secondary features incrementally |
| Frontend/backend incompatibility | Analytical components may work independently but fail in the application | Define stable input/output schemas before integration |
| Reproducibility issues | Instructor may be unable to execute the final product | Maintain dependencies, scripts, README and execution instructions throughout development |

---

## 10. Definition of Done

A component will be considered completed when:

1. its code is stored in the repository;
2. its inputs and outputs are documented;
3. it executes reproducibly;
4. its main assumptions and limitations are documented;
5. analytical components include an appropriate validation result;
6. the output can be consumed by the next component in the product pipeline;
7. relevant changes are reflected in the project documentation.

---

## 11. Final Implementation Objective

By Week 15, DepaRent should operate as an integrated Data Product in which a property owner can register a department, obtain an analytical characterization of its market position, review an expected rental-price estimate and district context, compare publication strategies, simulate selected property changes, and use these outputs to make a more informed publication decision.

The final product is intended as a **decision-support platform**, not as an official property appraisal system and not as a guarantee of rental price or rental time.
