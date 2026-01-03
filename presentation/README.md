# Presentation Materials - Circuit Breaker TCC

This folder contains all materials for the TCC (thesis) presentation in English.

## Contents

### 1. `slides.tex`
Complete LaTeX Beamer presentation slides with:
- **25 main slides** covering introduction, methodology, results, discussion, and conclusion
- **Backup slides** with additional technical details
- **CIn-UFPE theme** with institutional colors
- **High-quality figures** from the research paper
- **Clear structure** for 20-25 minute presentation

**To compile:**
```bash
pdflatex slides.tex
pdflatex slides.tex  # Run twice for proper references
```

**Required files:**
- All images from `../artigo_latex/images/` directory
- LaTeX packages: beamer, graphicx, booktabs, tikz, pgfplots

### 2. `PRESENTATION_GUIDE.md`
Comprehensive guide including:
- **Slide-by-slide speaking notes** with detailed explanations
- **Key messages to emphasize** during presentation
- **Anticipated Q&A** with suggested answers
- **Technical deep dive** on implementation details
- **Presentation tips** for body language, voice control, and timing
- **Time allocation** for each section (25 minutes total)

## Presentation Structure

### Section Breakdown

| Section | Slides | Time | Key Focus |
|---------|--------|------|-----------|
| **Introduction** | 1-8 | 5 min | Problem motivation, cascading failures, Circuit Breaker solution |
| **Methodology** | 9-14 | 5 min | Experimental design, 4 versions, 5 scenarios, metrics |
| **Results** | 15-23 | 10 min | Availability gains (+89pp), statistical validation, comparisons |
| **Discussion** | 24-27 | 3 min | User experience, resource protection, recommendations |
| **Conclusion** | 28-32 | 2 min | Contributions, limitations, future work |
| **Q&A** | 33 | Variable | Committee questions |

## Key Findings to Highlight

### Top Results
1. **+89.1 percentage points** availability improvement (10.3% → 99.4%)
2. **Up to 99%** failure reduction in severe scenarios
3. **Cliff's Delta = 0.500** (large effect size, p < 0.0001)
4. **V4 Composition** strategy provides optimal robustness
5. **380,000+ requests** analyzed across all experiments

### Visual Highlights
- Success rate heatmap showing V2/V4 superiority
- Availability comparison bars across scenarios
- Circuit Breaker state transition timeline
- Fallback contribution in severe failures

## How to Use These Materials

### For the Presenter (Humberto)

1. **Study the Guide:**
   - Read `PRESENTATION_GUIDE.md` thoroughly
   - Memorize key numbers: +89.1pp, 99%, Cliff's Delta 0.500
   - Practice anticipated Q&A responses

2. **Rehearse the Presentation:**
   - Practice 3× times minimum
   - Time each section (aim for 23-24 minutes)
   - Record yourself to identify improvement areas
   - Present to advisor or colleague for feedback

3. **Prepare Physically:**
   - Print slide notes as backup
   - Test equipment 1 hour before
   - Get good sleep night before
   - Arrive 30 minutes early

4. **During Presentation:**
   - Speak slowly and clearly
   - Make eye contact with committee
   - Use pointer to guide attention
   - Pause after key findings
   - Stay calm during questions

### For Committee Members

This presentation demonstrates:
- Rigorous experimental methodology
- Quantitative evaluation with statistical validation
- Comparative analysis of resilience strategies
- Practical recommendations for production systems
- Reproducible research framework

## Technical Requirements

### LaTeX Compilation
```bash
# Ensure you have TeX Live or MikTeX installed
pdflatex slides.tex
# If using bibliography (not in current version):
# bibtex slides
# pdflatex slides.tex
# pdflatex slides.tex
```

### Image Dependencies
All images are referenced from:
```
../artigo_latex/images/
```

Ensure the following images exist:
- `arch_tcc_mermaid_en.png` - Architecture diagram
- `academic_bars_availability_en.png` - Availability comparison
- `academic_heatmap_success_en.png` - Success rate heatmap
- `02_failure_reduction_en.png` - Failure reduction chart
- `cb_state_transitions.png` - State transition timeline
- `08_fallback_contribution_en.png` - Fallback contribution
- `v4-compositions-strategy.png` - V4 architecture
- `metric_correlation_heatmap.png` - Correlation matrix
- `01_success_rates_comparison_en.png` - Success rates comparison

## Presentation Language

**Language:** English  
**Audience:** Academic committee, software engineering researchers  
**Level:** Advanced undergraduate / graduate thesis defense  
**Style:** Formal academic presentation with clear technical explanations

## Tips for Success

### What to Emphasize
✅ Quantitative results with statistical validation  
✅ Practical implications for production systems  
✅ Clear comparison between strategies (V1-V4)  
✅ Large effect size (Cliff's Delta 0.500)  
✅ Dramatic availability improvement (+89pp)

### What to Avoid
❌ Reading slides verbatim  
❌ Getting lost in technical details  
❌ Rushing through results  
❌ Ignoring time constraints  
❌ Defensive responses to questions

### Key Soundbites
- "The Circuit Breaker transformed a 10% available system into a 99% available system."
- "This is not incremental improvement—this is transformative impact."
- "Fail-fast is systematically superior to hang-and-error."
- "V4 Composition provides the best of both worlds."

## License and Usage

These materials are part of Humberto Laff's TCC at Centro de Informática (CIn), Universidade Federal de Pernambuco (UFPE), under the supervision of Prof. Jamilson Ramalho Dantas.

## Contact

**Presenter:** Humberto Laff  
**Email:** hlaff@cin.ufpe.br  
**Advisor:** Prof. Jamilson Ramalho Dantas  
**Email:** jrd@cin.ufpe.br  
**Institution:** Centro de Informática (CIn) - UFPE

---

**Last Updated:** January 2026  
**Presentation Date:** [To be scheduled]  
**Duration:** ~25 minutes + Q&A

Good luck! 🎓
