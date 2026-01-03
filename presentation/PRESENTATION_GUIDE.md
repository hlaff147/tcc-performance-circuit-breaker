# TCC Presentation Guide - Circuit Breaker Pattern Evaluation
## Presentation Script and Content Explanation

**Author:** Humberto Laff  
**Advisor:** Prof. Jamilson Ramalho Dantas  
**Institution:** Centro de Informática (CIn) - UFPE  
**Date:** January 2026  
**Duration:** ~20-25 minutes  
**Language:** English

---

## Table of Contents

1. [Overview](#overview)
2. [Presentation Structure](#presentation-structure)
3. [Slide-by-Slide Speaking Notes](#slide-by-slide-speaking-notes)
4. [Key Messages to Emphasize](#key-messages-to-emphasize)
5. [Anticipated Questions & Answers](#anticipated-questions--answers)
6. [Technical Deep Dive](#technical-deep-dive)
7. [Presentation Tips](#presentation-tips)

---

## Overview

### Your Research in One Sentence
"This thesis provides the first comprehensive quantitative evaluation of the Circuit Breaker pattern in microservices, demonstrating availability improvements of up to 89 percentage points through controlled experimentation with 380,000+ requests across five realistic failure scenarios."

### Core Contribution
- **Empirical evidence** (not just theory) of Circuit Breaker effectiveness
- **Quantitative metrics** with statistical validation
- **Comparative analysis** of four resilience strategies
- **Reproducible methodology** using Docker + k6

### Target Audience
- Software engineers working with microservices
- System architects designing resilient systems
- Academic researchers in distributed systems
- DevOps/SRE professionals

---

## Presentation Structure

### Time Allocation (Total: ~25 minutes)

| Section | Duration | Purpose |
|---------|----------|---------|
| **Introduction** | 5 min | Motivate the problem and solution |
| **Methodology** | 5 min | Explain experimental design |
| **Results** | 10 min | Present findings with evidence |
| **Discussion** | 3 min | Interpret implications |
| **Conclusion** | 2 min | Summarize contributions |
| **Q&A** | Variable | Address committee questions |

---

## Slide-by-Slide Speaking Notes

### TITLE SLIDE (0:00 - 0:30)

**What to Say:**
> "Good morning/afternoon, distinguished committee members. My name is Humberto Laff, and I'm here to present my thesis titled 'Quantitative Evaluation of the Circuit Breaker Pattern in Microservices: An Empirical Study on Resilience and Performance,' conducted under the supervision of Professor Jamilson Ramalho Dantas at the Centro de Informática, UFPE."

**Tone:** Confident, clear, professional

---

### OUTLINE SLIDE (0:30 - 1:00)

**What to Say:**
> "This presentation is structured into five main sections. First, I'll introduce the problem of cascading failures in microservices. Second, I'll describe our experimental methodology. Third, I'll present our quantitative results. Fourth, I'll discuss the practical implications. Finally, I'll conclude with our contributions and future work directions."

**Purpose:** Set expectations, show organization

---

## SECTION 1: INTRODUCTION (1:00 - 6:00)

### Slide: Context - Microservices Architecture (1:00 - 2:30)

**What to Say:**
> "Microservices architecture has become the standard for building modern distributed systems. It offers clear benefits: independent development cycles, selective scalability, and organizational autonomy. However, this logical independence relies on synchronous communication—typically REST over HTTP—which creates strong temporal coupling between services."

**Pause for effect**

> "This coupling introduces a critical risk: cascading failures. When a dependent service experiences latency or unavailability, the consuming service waits until timeout, keeping threads blocked. Under load, this leads to thread pool exhaustion and system-wide collapse."

**Emphasize the business impact:**
> "The financial consequences are severe. Banking systems lose between $5,600 and $9,000 per minute of downtime. For large tech companies, losses can reach $450,000 per hour. With the exponential growth of digital transactions, resilience is not just a technical requirement—it's a business imperative."

**Key Message:** Problem is both technically challenging AND financially critical

**Visual Cue:** Point to the cost statistics in the slide

---

### Slide: The Problem - Cascading Failures (2:30 - 3:30)

**What to Say:**
> "Let me illustrate the cascading failure scenario with a concrete example from our experimental architecture."

**Walk through the sequence:**
> "Service A—our payment service—makes a synchronous REST call to Service B—an external acquirer service. When Service B experiences latency or failure, Service A's threads wait for the configured timeout—typically 2 to 3 seconds. Under high load with hundreds of concurrent requests, all available worker threads quickly become blocked. At this point, even requests to healthy endpoints fail because there are no threads available to process them. The entire service hangs."

**Emphasize:**
> "This is the essence of the cascading failure problem: a localized issue in one dependency can bring down the entire system."

**Visual Cue:** Point to the architecture diagram showing the dependency chain

---

### Slide: The Solution - Circuit Breaker Pattern (3:30 - 4:30)

**What to Say:**
> "The Circuit Breaker pattern addresses this problem using a simple but powerful analogy: the electrical fuse in your home."

**Explain the analogy:**
> "Just as an electrical fuse 'trips' when it detects a dangerous power surge—cutting off electricity to prevent a fire—the Circuit Breaker in software 'trips' when it detects a 'failure surge,' halting requests to a failing service and preventing system-wide collapse."

**Explain the state machine:**
> "The Circuit Breaker operates as a state machine with three states:
> - **Closed state**: Normal operation, all traffic flows through
> - **Open state**: Fail-fast mode, requests are immediately rejected with a fallback response
> - **Half-Open state**: Recovery probing, a limited number of requests are allowed to test if the service has recovered"

**Key benefits:**
> "This provides four critical benefits: Fail-Fast responses, Resource Protection by releasing threads immediately, Graceful Degradation through fallback mechanisms, and Auto-Recovery through self-healing probes."

**Visual Cue:** Use hand gestures to illustrate state transitions

---

### Slide: Research Objectives (4:30 - 6:00)

**What to Say:**
> "Despite extensive literature on the Circuit Breaker pattern, there is a significant gap in quantitative experimental studies. Most available documentation is limited to conceptual descriptions or trivial examples. My research addresses this gap by asking:"

**Read the research question clearly:**
> "What is the *quantitative* impact of the Circuit Breaker pattern on microservices resilience and performance?"

**Enumerate specific goals:**
> "To answer this, I defined five specific objectives:
> 1. Measure availability improvement across diverse failure scenarios
> 2. Compare Circuit Breaker against Retry and Composition strategies
> 3. Quantify response time reduction with statistical confidence
> 4. Provide rigorous statistical validation using effect size measures
> 5. Demonstrate resource protection benefits"

**Contribution statement:**
> "This work represents the first comprehensive empirical study providing robust quantitative evidence of Circuit Breaker effectiveness in microservices."

**Tone:** Confident, emphasizing the novelty and rigor

---

## SECTION 2: METHODOLOGY (6:00 - 11:00)

### Slide: Experimental Architecture (6:00 - 7:00)

**What to Say:**
> "To conduct this evaluation, I designed and implemented a Proof of Concept simulating a microservices ecosystem with synchronous dependency."

**Explain the architecture:**
> "The POC consists of two Spring Boot microservices, both containerized with Docker. The payment-service orchestrates the payment flow and synchronously consumes the acquirer-service via Spring Cloud OpenFeign. The acquirer-service simulates an external payment gateway with configurable behavior—it can operate normally, inject latency, or simulate failures."

**Explain the design choice:**
> "Critically, this POC is intentionally minimalistic—there's no database, no cache, no authentication. This isolation strategy ensures that the Circuit Breaker is the sole variable of interest. Any performance differences we observe can be directly attributed to the resilience pattern, not to confounding factors."

**Testing infrastructure:**
> "Load testing was performed using Grafana k6, a modern load testing tool that generates realistic HTTP traffic patterns."

**Visual Cue:** Point to the architecture diagram showing the data flow

---

### Slide: Four Service Versions (7:00 - 8:30)

**What to Say:**
> "I implemented four versions of the payment-service, each representing a different resilience strategy."

**Walk through each version:**
> "**Version 1 (Baseline)**: This is our control group—basic timeouts only, no resilience patterns. It represents what many production systems look like today.
>
> **Version 2 (Circuit Breaker)**: Implements the Circuit Breaker using Resilience4j, a lightweight fault tolerance library. When the circuit opens, it returns an HTTP 202 'Accepted' response as a fallback.
>
> **Version 3 (Retry)**: Implements exponential backoff retry with three attempts. This is a common pattern developers use, but we'll see it has significant limitations.
>
> **Version 4 (Composition)**: Combines Retry and Circuit Breaker in a layered approach. The Retry layer wraps the Circuit Breaker call, allowing the system to absorb transient jitters through retries while still providing hard cutoffs for persistent failures through the Circuit Breaker."

**Explain V2 configuration:**
> "For Version 2, I configured the Circuit Breaker with carefully selected thresholds based on the criticality of the payment domain:
> - Failure threshold of 50%—indicating the dependency is no longer reliable
> - Slow call threshold of 70%—prioritizing thread protection
> - Sliding window of 20 requests—providing robust statistical samples
> - Open state duration of 15 seconds—aligned with cloud load balancer recovery times"

**Visual Cue:** Point to the configuration details in the slide

---

### Slide: Test Scenarios (8:30 - 9:30)

**What to Say:**
> "To evaluate these versions, I designed five realistic failure scenarios using Grafana k6. These scenarios simulate diverse failure patterns encountered in production environments."

**Walk through scenarios:**
> "**Normal scenario**: Our baseline—100% healthy service for 10 minutes with 100 virtual users. This establishes the performance ceiling.
>
> **Degradation scenario**: Simulates a gradual failure increase from 5% to 50% over 13 minutes with 100-200 virtual users. This represents a service slowly degrading under load.
>
> **Bursts scenario**: Three intermittent 1-minute bursts of 100% failure over 13 minutes. This simulates network partitions or brief outages.
>
> **Catastrophe scenario**: A complete 100% failure for 5 minutes in the middle of a 13-minute test. This is the 'worst case' scenario.
>
> **Extreme Unavailability scenario**: 75% of the service is offline throughout the entire 9-minute test. This represents a severely degraded state."

**Emphasize scale:**
> "Across all scenarios and versions, we analyzed over 380,000 requests—providing robust statistical power."

**Visual Cue:** Point to the scenario characteristics in the table

---

### Slide: Key Concepts (9:30 - 11:00)

**What to Say:**
> "Before presenting results, I need to define three key concepts."

**Perceived Availability:**
> "First, **Perceived Availability**. This is the fraction of requests resulting in either a successful outcome—HTTP 200 or 201—or a gracefully degraded outcome delivered through the fallback mechanism—HTTP 202. This metric reflects user-visible continuity of service."

**Explain HTTP 202:**
> "The use of HTTP 202 'Accepted' is deliberate. According to RFC 9110, HTTP 202 indicates that the request has been accepted for processing but processing has not been completed. In our context, this maps to a 'scheduled payment' or 'queued for retry' pattern—maintaining semantic honesty while providing graceful degradation."

**Load Amplification:**
> "Second, **Load Amplification Factor**. This measures the ratio between total requests sent by a resilient version versus the baseline. It quantifies the additional pressure exerted on downstream dependencies by retry mechanisms. This becomes critical when analyzing Victim Denial of Service risks."

**Total requests:**
> "Finally, I want to emphasize the scale: over 380,000 requests were analyzed across all experimental runs, providing robust statistical confidence."

**Visual Cue:** Point to the formulas and emphasize the metrics

---

## SECTION 3: RESULTS (11:00 - 21:00)

### Slide: Availability Comparison - All Scenarios (11:00 - 12:00)

**What to Say:**
> "Now, let's examine the results. This chart shows Perceived Availability across all five scenarios for all four versions."

**Point to the chart:**
> "Notice the clear visual pattern: V2—Circuit Breaker—and V4—Composition—consistently outperform V1—Baseline—and V3—Retry across all failure scenarios. The difference is most pronounced in severe failure scenarios like Catastrophe and Extreme Unavailability."

**Key observation:**
> "In the Normal scenario, all versions perform identically at 100%, confirming that the Circuit Breaker introduces zero overhead under healthy conditions. However, as failure severity increases, the gap widens dramatically."

**Transition:**
> "Let me quantify these differences more precisely."

**Visual Cue:** Use a pointer or hand to trace the bars from left to right

---

### Slide: Key Results - Availability Gains (12:00 - 13:30)

**What to Say:**
> "This table presents the precise Perceived Availability percentages and gains."

**Walk through critical rows:**
> "In the **Bursts scenario**, V1 achieved only 62.9% availability, while V2 and V4 reached 96.7% and 96.6% respectively—a gain of 33.8 percentage points.
>
> In the **Catastrophe scenario**, V1 registered just 35.7%, while V2 and V4 maintained 95.1%—a gain of 59.4 percentage points.
>
> Most dramatically, in the **Extreme Unavailability scenario**, V1 achieved only 10.3% availability—effectively a system outage. V2 and V4, however, achieved 99.1% and 99.4% respectively—a gain of 89.1 percentage points."

**Emphasize the transformation:**
> "Let me be clear about what this means: The Circuit Breaker transformed a system with only 10% availability—a system that is essentially down—into a system with 99% availability—a system that is fully operational from the user's perspective."

**Pause for impact**

> "This is not a marginal improvement. This is the difference between a catastrophic outage and business continuity."

**Tone:** Strong, confident, let the numbers speak

**Visual Cue:** Point to the Extreme Unavailability row and the +89.1pp gain

---

### Slide: Failure Reduction (13:30 - 14:30)

**What to Say:**
> "Beyond availability, let's examine failure reduction—the percentage decrease in HTTP 500 errors."

**Point to the chart:**
> "This chart shows failure rates and the reduction percentages achieved by resilient versions compared to V1 baseline. In critical scenarios like Catastrophe and Extreme Unavailability, failure reduction exceeded 91%."

**Explain the mechanism:**
> "How does the Circuit Breaker achieve this? By transforming HTTP 500 errors into HTTP 202 fallback responses. In the Catastrophe scenario, 62.1% of V2's responses originated from the fallback mechanism—effectively converting fatal errors into meaningful outcomes for end users."

**Key insight:**
> "This shift in failure mode—from 'hard failure' to 'graceful degradation'—is fundamental to resilient system design."

**Visual Cue:** Point to the reduction percentages on the chart

---

### Slide: Success Rate Heatmap (14:30 - 15:30)

**What to Say:**
> "This heatmap provides a visual summary of success rates across all scenarios and versions. Each cell represents the success rate for a specific scenario-version combination."

**Explain the color coding:**
> "Green indicates high success rates—above 90%—while red indicates critical failures. Notice the stark contrast: V1 and V3 show significant red zones in severe scenarios, while V2 and V4 remain predominantly green."

**Point to specific cells:**
> "Look at the Extreme Unavailability row: V1 shows deep red—only 10.3% success—while V2 and V4 show bright green—over 99% success. This visual pattern confirms our quantitative findings."

**Purpose:**
> "This heatmap serves as a 'dashboard' view—instantly communicating where each strategy succeeds or fails."

**Visual Cue:** Point to contrasting cells between V1 and V2/V4

---

### Slide: Statistical Validation (15:30 - 17:00)

**What to Say:**
> "Now, let me address the statistical rigor of these findings. It's not enough to show that V2 performs better than V1—we must demonstrate that this difference is statistically significant and practically relevant."

**Mann-Whitney U Test:**
> "First, I applied the Mann-Whitney U test, a non-parametric test comparing two independent samples. For V1 versus V2 globally, the p-value is less than 0.0001—highly significant. This means there is less than a 0.01% probability that the observed differences occurred by chance."

**Cliff's Delta:**
> "Second, I calculated Cliff's Delta, a non-parametric effect size measure. The result is 0.500, which classifies as a **large effect size** according to established thresholds. This confirms substantial practical relevance—the differences we observe matter in real-world systems."

**Response Time:**
> "Concretely, V1 exhibited a mean response time of 1281.44 milliseconds, while V2 achieved 437.67 milliseconds—a reduction of 843.77 milliseconds. The 95% confidence interval for this difference ranges from 823 to 864 milliseconds, demonstrating high precision in our estimate."

**Conclusion:**
> "In summary: The Circuit Breaker provides robust latency reduction with high statistical confidence and large practical effect."

**Tone:** Precise, academic, emphasizing rigor

**Visual Cue:** Point to the statistical metrics and confidence intervals

---

### Slide: Circuit Breaker State Transitions (17:00 - 18:00)

**What to Say:**
> "To understand the dynamic behavior of the Circuit Breaker, I analyzed latency profiles over time for each version."

**Explain the visualization:**
> "This multi-panel chart shows average latency over time on a logarithmic scale. For V2 and V4, the red shaded areas indicate periods where the Circuit Breaker is in the OPEN state—fail-fast mode with fallback active."

**Point to key patterns:**
> "Notice the dramatic contrast: V1 shows sustained high latency during failures—those flat lines at 2,000 to 3,000 milliseconds represent threads waiting for timeouts. V2 and V4, however, show immediate drops to sub-millisecond latencies when the circuit opens."

**Explain fail-fast:**
> "This is the 'fail-fast' benefit in action: instead of waiting for inevitable timeouts, the system immediately returns a fallback response, releasing resources and maintaining responsiveness."

**Visual transition behavior:**
> "You can also observe the Half-Open state transitions—those brief spikes where the circuit is probing for recovery. If probes succeed, the circuit closes and latency returns to normal. If probes fail, the circuit reopens."

**Visual Cue:** Trace the latency lines with your finger or pointer

---

### Slide: Fallback Contribution (18:00 - 18:45)

**What to Say:**
> "This chart illustrates the composition of responses for V2 and V4 in severe scenarios."

**Explain the breakdown:**
> "In the Catastrophe scenario, 62.1% of responses came from the fallback mechanism—HTTP 202. In Extreme Unavailability, this reaches 99.1%."

**Key insight:**
> "This demonstrates that the fallback mechanism is not a 'nice-to-have' feature—it is **essential** for resilience. Without it, V1 users experienced 62% hard failures. With it, V2 users experienced 62% graceful degradations that enabled business continuity."

**Transition:**
> "This raises an important question: How does the Circuit Breaker compare to the Retry pattern?"

**Visual Cue:** Point to the percentages showing fallback contribution

---

### Slide: V3 (Retry) vs V2 (Circuit Breaker) (18:45 - 19:30)

**What to Say:**
> "Version 3 implements exponential backoff retry with three attempts—a common pattern many developers use. However, our results reveal significant risks."

**V3 Risks:**
> "Retry introduces **Load Amplification**: each failed request triggers three retry attempts, creating persistent pressure on the failing service. This phenomenon is known as 'Victim Denial of Service'—retry traffic from many clients prevents a struggling service from recovering, effectively acting as a self-inflicted DDoS attack."

**V3 inadequacy:**
> "For **persistent failures**, retry is inadequate. It optimistically assumes failures are transient, but when failures persist, retry simply multiplies the load without solving the problem."

**V2 Benefits:**
> "Circuit Breaker, in contrast, provides **Fail-Fast Protection**: immediate fallback with no retry pressure. This allows the failing service space to recover."

**V4 Solution:**
> "Version 4—Composition—combines the best of both worlds: retry absorbs transient jitters, while the Circuit Breaker protects against persistent failures."

**Visual Cue:** Point to the contrasting alertblock and exampleblock

---

### Slide: V4 Composition Strategy (19:30 - 20:30)

**What to Say:**
> "Let me elaborate on the V4 Composition strategy, which emerged as the most robust approach."

**Explain the architecture:**
> "V4 wraps the Circuit Breaker call inside a Retry layer. When a failure occurs, the system first attempts retries. If the failure is transient—a brief network blip—the retry succeeds, and the circuit never trips. If the failure persists, retries exhaust, and the Circuit Breaker trips, activating the fallback."

**Key advantages:**
> "This layered approach provides four key advantages:
> 1. Absorbs momentary glitches without unnecessary circuit state changes
> 2. Maintains hard cutoffs for persistent failures
> 3. Achieved the highest availability—99.4%—in Extreme Unavailability
> 4. Demonstrated the highest robustness across all scenarios"

**Real-world relevance:**
> "In production systems, transient failures are common—brief network jitters, momentary CPU spikes, container restarts. V2 would trip the circuit for these minor issues, potentially causing unnecessary fallbacks. V4 handles them gracefully through retries, reserving the circuit trip for true persistent outages."

**Recommendation:**
> "Based on our findings, **V4 is the recommended strategy for mission-critical microservices**."

**Visual Cue:** Point to the diagram showing the layered architecture

---

### Slide: Metric Correlations (Optional - if time permits)

**What to Say:**
> "This correlation heatmap analyzes relationships between key performance metrics across all versions and scenarios."

**Key finding:**
> "Notice the strong negative correlation between Fallback Rate and Failure Rate—as fallback usage increases, failures decrease proportionally. This validates the effectiveness of the fallback mechanism."

**Additional insight:**
> "We also observe correlations between latency and circuit state—when the circuit opens, latency drops dramatically, confirming the fail-fast behavior."

**Visual Cue:** Point to the correlation coefficients

---

## SECTION 4: DISCUSSION (20:30 - 23:30)

### Slide: Graceful Degradation - Beyond Numbers (20:30 - 21:30)

**What to Say:**
> "Beyond the quantitative metrics, I want to discuss the qualitative impact of graceful degradation on user experience."

**Contrast the experiences:**
> "Consider two users during a backend failure:
>
> **User A (V1 Baseline)**: Submits a payment request. Waits 2-3 seconds. Receives an HTTP 500 error: 'Service Unavailable.' No feedback, no alternatives, no understanding of what went wrong.
>
> **User B (V2/V4 Circuit Breaker)**: Submits a payment request. Receives an immediate response—less than 1 millisecond—with HTTP 202: 'Payment Accepted for Processing.' The frontend can display: 'Your payment has been scheduled and will be processed shortly. You'll receive a confirmation email within 30 minutes.'"

**Psychological impact:**
> "From a psychological perspective, fail-fast is systematically superior to 'hang and error.' Research in human-computer interaction shows that users prefer immediate feedback—even if it's partial—over long waits followed by failures."

**Business value:**
> "From a business perspective, this maintains **operational continuity** during backend failures. The user's journey doesn't end in frustration—they receive acknowledgment and can continue using other parts of the application."

**Tone:** Empathetic, user-focused

**Visual Cue:** Use hand gestures to emphasize the contrast between the two experiences

---

### Slide: Resource Protection - Thread Pool (21:30 - 22:30)

**What to Say:**
> "Now let's discuss a critical but less visible benefit: thread pool protection."

**V1 Problem:**
> "In V1, each request to a failing dependency occupies a worker thread for the full 2-second timeout. Under high load—let's say 200 concurrent users—all available threads quickly become blocked waiting for timeouts. Once the thread pool is exhausted, the entire service hangs. **Critically, even healthy endpoints become unavailable**—requests that don't depend on the failing service also fail because there are no threads to process them."

**Cascading failure:**
> "This is the essence of cascading failure: a localized issue in one dependency brings down the entire service, affecting all operations."

**V2 Solution:**
> "V2's Circuit Breaker detects the failures, opens the circuit, and enters fail-fast mode. Threads are released in under 1 millisecond. The thread pool remains available to serve other operations. The service stays healthy."

**Quantitative evidence:**
> "In our experiments, V1 experienced complete thread pool saturation during Catastrophe scenarios, while V2 maintained over 95% thread availability throughout."

**Key message:**
> "Resource protection is not just about performance—it's about system **survival**."

**Tone:** Technical, emphasizing system-level implications

**Visual Cue:** Use hand gestures to illustrate blocked vs. free threads

---

### Slide: Architectural Recommendations (22:30 - 23:30)

**What to Say:**
> "Based on our experimental findings, I've developed architectural recommendations for selecting the appropriate resilience strategy."

**Walk through the table:**
> "**V1 Baseline** is acceptable only for non-critical internal tools with highly reliable dependencies. The risk is cascading failure and thread pool starvation.
>
> **V2 Circuit Breaker** is best for external APIs, third-party services, and unreliable gateways. The risk is unnecessary fallbacks triggered by minor transient jitters.
>
> **V3 Retry** is appropriate for database operations and idempotent transient failures—like a brief lock contention. The risk is load amplification and Victim Denial of Service for persistent failures.
>
> **V4 Composition** is the recommended strategy for mission-critical operations like payments and high-availability services. The only risk is configuration complexity—requiring careful tuning of both retry and circuit breaker parameters."

**Best practice:**
> "The key best practice: **Combine patterns**. Do not use Retry alone for persistent failures. Wrap Retry inside a Circuit Breaker to prevent resource exhaustion while gracefully handling transient issues."

**Visual Cue:** Point to each row in the table as you discuss it

---

### Slide: Recovery Time Analysis (Optional - if time permits)

**What to Say:**
> "One interesting finding concerns recovery time—the delay between dependency recovery and circuit closure."

**Explain the variation:**
> "In the Catastrophe scenario, recovery took 212 seconds after the dependency resumed. This substantial delay results from the sliding window requiring new healthy samples and conservative probe frequency. However, in the Bursts scenario, recovery was nearly instantaneous—0.01 seconds—because the circuit hadn't yet opened or was already probing."

**Trade-off:**
> "This illustrates a fundamental trade-off: conservative recovery prevents 'flapping'—rapid open-close-open cycles—but increases downtime. Aggressive recovery reduces downtime but risks flapping and overwhelming a fragile recovering service."

**Recommendation:**
> "Our configuration—15-second wait duration, 5 probe calls—balances these concerns for payment systems, but different domains may require different tuning."

**Visual Cue:** Point to the recovery time numbers

---

## SECTION 5: CONCLUSION (23:30 - 25:30)

### Slide: Summary of Contributions (23:30 - 24:15)

**What to Say:**
> "Let me now summarize the contributions of this work."

**Enumerate clearly:**
> "First, this thesis provides **robust empirical evidence** of Circuit Breaker impact across five realistic failure scenarios—moving beyond conceptual descriptions to quantitative measurement.
>
> Second, it offers a **quantitative comparison** of Circuit Breaker versus Retry versus Composition strategies—clarifying when each approach is appropriate.
>
> Third, it provides **rigorous statistical validation** with large effect size—Cliff's Delta of 0.500—ensuring practical relevance.
>
> Fourth, it establishes a **reproducible methodology** using Docker and k6—enabling other researchers to replicate and extend this work.
>
> Fifth, it delivers **practical recommendations** grounded in empirical data—guiding production system design."

**Key finding:**
> "The central finding: Circuit Breaker improved availability from 10.3% to 99.4% in extreme failures—a gain of 89.1 percentage points. This is not incremental improvement; this is transformative impact."

**Tone:** Confident, summarizing achievements

---

### Slide: Main Results Recap (24:15 - 25:00)

**What to Say:**
> "To recap the main results across four dimensions:"

**Availability:**
> "Availability gains reached up to 89 percentage points, consistent across all scenarios, with V4 Composition demonstrating the highest robustness."

**Failure Reduction:**
> "Failure reduction reached up to 99%, achieved by converting HTTP 500 errors into HTTP 202 fallback responses."

**Response Time:**
> "Response time reduction averaged 843 milliseconds, with high confidence—p-value less than 0.0001—and large effect size."

**Resource Protection:**
> "Resource protection was maintained throughout: thread pools preserved, fail-fast responses under 1 millisecond, and zero overhead under healthy conditions."

**Conclusion:**
> "These results collectively demonstrate that the Circuit Breaker is **essential** for mission-critical synchronous microservices."

**Visual Cue:** Point to each quadrant as you discuss it

---

### Slide: Practical Recommendations (25:00 - 25:45)

**What to Say:**
> "Based on these findings, I offer four practical recommendations for practitioners:"

**Enumerate clearly:**
> "**First**, combine patterns. Do not use Retry alone for persistent failures. Wrap it inside a Circuit Breaker—the V4 strategy.
>
> **Second**, use meaningful fallbacks. Return HTTP 202 or 204 to indicate acceptance for later processing, not generic 500 errors.
>
> **Third**, configure conservative probing. Set the Half-Open state with a small number of permitted calls—like our 5 probes—to avoid overwhelming a recovering dependency.
>
> **Fourth**, monitor and tune continuously. Observe Circuit Breaker metrics—state, failure rate, recovery time—and adjust thresholds based on real production patterns."

**Closing:**
> "These recommendations are not theoretical—they are grounded in empirical evidence from over 380,000 requests."

**Tone:** Practical, actionable

---

### Slide: Limitations (25:45 - 26:15)

**What to Say:**
> "Like all research, this work has limitations that should be acknowledged."

**Be transparent:**
> "First, this is a **simplified Proof of Concept**—no database, cache, or complex business logic. Real production systems have additional complexity layers.
>
> Second, the **local environment** lacks real network latency, geographic distribution, and infrastructure failures.
>
> Third, the **synthetic load** uses uniform k6 patterns, not real user behavior with varied request types and think times.
>
> Fourth, only a **single Circuit Breaker configuration** was tested—parameter sensitivity analysis remains for future work."

**External validity:**
> "That said, while absolute numbers may vary in production environments, the **direction** of benefits—improved availability, reduced failures, protected resources—should remain consistent. The fundamental physics of synchronous communication don't change."

**Tone:** Honest, balanced, scientific

---

### Slide: Future Work (26:15 - 27:00)

**What to Say:**
> "This research opens several promising directions for future work."

**Enumerate opportunities:**
> "First, evaluating **hybrid strategies** combining Circuit Breaker, Retry, and Rate Limiting in multi-layer compositions.
>
> Second, conducting **parameter sensitivity analysis** to understand how different threshold configurations impact performance.
>
> Third, integrating **Chaos Engineering** frameworks like LitmusChaos or Chaos Mesh for automated failure injection in Kubernetes.
>
> Fourth, comparing library-level Circuit Breakers against **Service Mesh** implementations like Istio and Linkerd.
>
> Fifth, exploring **asynchronous architectures** using Kafka or RabbitMQ and their resilience characteristics.
>
> Sixth, investigating **adaptive Circuit Breaking** using machine learning to dynamically adjust thresholds based on real-time observability.
>
> Seventh, evaluating multi-cloud and geo-distributed deployments to understand geographic failure propagation."

**Tone:** Forward-looking, enthusiastic

---

### Slide: Final Message (27:00 - 27:45)

**What to Say:**
> "Let me conclude with a clear final message:"

**Read slowly and clearly:**
> "The Circuit Breaker pattern is **essential** for mission-critical synchronous microservices."

**Pause**

> "Our empirical study provides robust quantitative evidence that the Circuit Breaker dramatically improves availability—by up to 89 percentage points—reduces failures by up to 99%, protects system resources, and enables graceful degradation."

**Recommendation:**
> "For production systems, I strongly recommend the **V4 Composition strategy**—combining Retry and Circuit Breaker to handle both transient and persistent failures."

**Closing:**
> "This research moves the field beyond conceptual understanding to empirical validation. We now have quantitative evidence to guide resilient system design."

**Tone:** Strong, confident, conclusive

---

### Slide: Thank You / Q&A (27:45+)

**What to Say:**
> "Thank you for your attention. I'm now happy to answer your questions."

**Body language:** Open posture, make eye contact with committee members

---

## Key Messages to Emphasize

### Top 5 Takeaways

1. **Dramatic Availability Improvement**: +89.1pp gain in extreme scenarios
2. **Statistical Rigor**: Large effect size (Cliff's Delta = 0.500), p < 0.0001
3. **V4 Composition is Superior**: Best of retry + circuit breaker
4. **Resource Protection is Critical**: Prevents thread pool exhaustion
5. **Empirical Evidence Fills Gap**: First comprehensive quantitative study

### Memorable Soundbites

- "The Circuit Breaker transformed a 10% available system into a 99% available system."
- "This is not incremental improvement—this is transformative impact."
- "Fail-fast is systematically superior to hang-and-error."
- "Thread pool protection is not just about performance—it's about system survival."
- "Do not use Retry alone for persistent failures—wrap it inside a Circuit Breaker."

---

## Anticipated Questions & Answers

### Q1: Why did you choose Resilience4j over other Circuit Breaker libraries?

**Answer:**
> "Excellent question. I chose Resilience4j for three primary reasons. First, it's the recommended successor to Netflix Hystrix, which entered maintenance mode in 2018. Second, it offers a modular, functional design with a smaller footprint—important for microservices where dependency size matters. Third, it provides first-class support for Spring Boot integration with declarative annotations, simplifying implementation. That said, the principles evaluated in this thesis apply to any Circuit Breaker implementation—the pattern itself is library-agnostic."

---

### Q2: How did you determine the Circuit Breaker threshold values (50%, 70%, 20 requests, etc.)?

**Answer:**
> "The thresholds were selected based on domain criticality and empirical tuning. The 50% failure threshold represents a conservative balance—lower values like 20% might cause flapping due to transient jitters, while higher values like 80% would delay protection. The 70% slow call threshold prioritizes thread protection, recognizing that slow calls are often more dangerous than failures because they cause silent resource exhaustion. The 20-request sliding window provides a robust statistical sample while remaining responsive. The 15-second open duration aligns with standard cloud load balancer recovery times. These values reflect payment domain requirements, but different domains—like video streaming or IoT—might warrant different tuning. Parameter sensitivity analysis is identified as future work."

---

### Q3: Your POC is simplified—no database, no cache. How would these affect results?

**Answer:**
> "This is an intentional design choice to isolate the Circuit Breaker as the sole variable. In real systems with databases and caches, you'd likely see **additional** resilience benefits. For example, database connection pools face the same thread exhaustion risks—Circuit Breakers protecting database calls would prevent pool depletion. Similarly, cache misses during failures could amplify load—Circuit Breakers would mitigate this. However, you'd also introduce new complexity: database transactions, cache consistency, distributed tracing. The fundamental principle remains: synchronous dependencies under failure create cascading risks, and Circuit Breakers mitigate those risks. Our simplified POC provides a lower bound on benefits; production systems would likely see amplified gains due to additional failure modes."

---

### Q4: What about false positives? Could the Circuit Breaker trip unnecessarily during traffic spikes?

**Answer:**
> "Great question—this addresses the trade-off between protection and availability. False positives can occur if thresholds are too aggressive. For example, a sudden traffic spike might cause transient 429 'Too Many Requests' responses, triggering the circuit inappropriately. I mitigated this in two ways. First, the 50% failure threshold requires sustained errors, not isolated incidents. Second, the 20-request sliding window averages over multiple requests, reducing outlier impact. Third—and most importantly—the V4 Composition strategy addresses this directly: the Retry layer absorbs transient spikes, and only persistent failures trip the circuit. In production systems, I recommend monitoring circuit state transitions and adjusting thresholds iteratively based on observability data. Tools like Prometheus and Grafana can alert on flapping behavior, indicating thresholds need tuning."

---

### Q5: How does this compare to Service Mesh approaches like Istio?

**Answer:**
> "Service Meshes like Istio and Linkerd provide infrastructure-level Circuit Breakers using sidecar proxies—typically Envoy. The key difference is **where** the logic lives. Library-level implementations like Resilience4j operate in-process, providing application-aware logic—for example, different thresholds for different endpoints or business-logic-driven fallbacks. Service Meshes operate at the network layer, language-agnostic but less granular. The advantage of Service Meshes is centralized policy management and zero application code changes. The advantage of libraries is fine-grained control and business context awareness. In practice, **both can coexist**: Service Mesh provides network-level protection, while libraries provide application-level resilience. My thesis focuses on library-level implementation, but comparing these approaches is identified as future work. I suspect optimal production architectures will use **defense in depth**—layers at both infrastructure and application levels."

---

### Q6: What is the impact of the 15-second recovery time? Isn't that too slow?

**Answer:**
> "The 15-second wait duration before transitioning from Open to Half-Open represents a trade-off between recovery speed and stability. Shorter durations—like 5 seconds—would reduce downtime but risk 'flapping': the circuit opens, closes prematurely, immediately reopens, creating instability. Our 212-second recovery in the Catastrophe scenario includes both the 15-second wait *and* the time for the sliding window to accumulate healthy samples. For the payment domain, this conservative approach is appropriate—we prioritize stability over rapid recovery. However, for real-time systems like video streaming, you might configure 5-second wait durations. Additionally, the V4 Composition strategy mitigates this concern: the Retry layer continues attempting requests even when the circuit is open, enabling faster recovery when the dependency resumes. Future work could explore adaptive wait durations using PID controllers or machine learning to dynamically adjust based on failure patterns."

---

### Q7: How did you ensure statistical validity with only 5 scenarios?

**Answer:**
> "Statistical validity comes from three sources. First, **sample size**: over 380,000 total requests across all scenarios and versions provides massive statistical power. Second, **scenario diversity**: the five scenarios cover a broad spectrum—from 100% health to 75% unavailability, transient bursts to persistent outages. This diversity ensures we're not cherry-picking favorable conditions. Third, **rigorous analysis**: I applied multiple statistical tests—Mann-Whitney U for pairwise comparison, ANOVA for multi-group analysis, and Cliff's Delta for effect size. The p-value of less than 0.0001 indicates results are highly unlikely due to chance. The Cliff's Delta of 0.500 confirms large practical effect. Additionally, I used **controlled experiments**: all versions were tested under identical conditions using the same k6 scenarios, eliminating confounding variables. The methodology section details reproducibility—other researchers can replicate these experiments and validate findings."

---

### Q8: Why HTTP 202 instead of HTTP 503 for fallback responses?

**Answer:**
> "This is a semantic choice grounded in RFC 9110. HTTP 503 'Service Unavailable' indicates the server is currently unable to handle the request—implying user should retry later. HTTP 202 'Accepted' indicates the request has been accepted for processing but processing is not complete—implying the server will handle it asynchronously. For payment systems, HTTP 202 maps naturally to 'scheduled payment' or 'queued for retry'—the user's intent is acknowledged, and the system commits to eventual processing. This maintains semantic honesty and provides a better user experience. The frontend can display: 'Your payment is being processed. You'll receive confirmation shortly.' In contrast, HTTP 503 communicates failure without acknowledgment. That said, the specific status code is a design decision—the core principle is **graceful degradation through fallback**, regardless of the exact HTTP semantics. Some systems might prefer HTTP 429 'Too Many Requests' or custom 2xx codes."

---

### Q9: What about data consistency? If the fallback accepts a payment, how do you ensure it's eventually processed?

**Answer:**
> "Excellent question—this touches on eventual consistency patterns. In our POC, the HTTP 202 fallback is a **signal** that the system has accepted the request for later processing—it doesn't actually persist or guarantee processing. In a production system, you'd implement this using **message queues** or **event sourcing**. When the Circuit Breaker trips, instead of immediately calling the acquirer, the payment service would publish an event to a Kafka topic or RabbitMQ queue. A background worker would consume these events and retry the acquirer call asynchronously, with exponential backoff and dead-letter queues for failed messages. This pattern—often called 'Transactional Outbox' or 'Saga'—ensures at-least-once delivery. Database transactions would record the payment intent before returning HTTP 202, guaranteeing durability. This introduces additional complexity but is essential for mission-critical financial systems. My thesis focuses on the Circuit Breaker's impact on synchronous communication; asynchronous persistence patterns are complementary and identified as future work."

---

### Q10: How would this work in a multi-region deployment?

**Answer:**
> "Multi-region deployments introduce fascinating additional considerations. Each region would have its own Circuit Breaker instance, potentially with region-specific configurations based on local failure patterns. For example, if Region A has an unreliable network, you might configure a more aggressive failure threshold. The challenge is **coordinated failure detection**: if the acquirer service is globally down, you want all regions to trip simultaneously to avoid wasted retries. This could be achieved using **distributed coordination** via shared state in Redis or etcd, or **service mesh** implementations like Istio's global traffic management. Alternatively, you could use **client-side load balancing** where each payment service instance maintains Circuit Breakers for each acquirer region, routing to healthy regions. Geographic distribution also affects recovery: latency-based health checks might incorrectly trip circuits due to normal cross-region delays. This is identified as future work—evaluating Circuit Breaker behavior in geo-distributed environments with realistic network characteristics."

---

## Technical Deep Dive

### Circuit Breaker State Machine Logic

**Closed State:**
- All requests pass through normally
- Sliding window tracks success/failure rates
- If `(failures / total) > failureRateThreshold` (50%) OR `(slowCalls / total) > slowCallRateThreshold` (70%), transition to OPEN

**Open State:**
- All requests immediately fail-fast with fallback (HTTP 202)
- No calls to downstream service
- After `waitDurationInOpenState` (15s), automatically transition to HALF_OPEN

**Half-Open State:**
- Allow `permittedNumberOfCallsInHalfOpenState` (5) probe requests
- If all probes succeed, transition to CLOSED
- If any probe fails, transition back to OPEN

### Resilience4j Configuration (V2)

```yaml
resilience4j.circuitbreaker:
  instances:
    acquirerService:
      slidingWindowType: COUNT_BASED
      slidingWindowSize: 20
      minimumNumberOfCalls: 10
      failureRateThreshold: 50
      slowCallRateThreshold: 70
      slowCallDurationThreshold: 1000ms
      waitDurationInOpenState: 15s
      permittedNumberOfCallsInHalfOpenState: 5
      automaticTransitionFromOpenToHalfOpenEnabled: true
      registerHealthIndicator: true
```

### V4 Composition Architecture

```java
@Retry(name = "acquirerRetry")
public PaymentResponse processPayment(PaymentRequest request) {
    return feignClient.process(request); // Feign client call is wrapped by CB
}

// Feign client method is decorated with @CircuitBreaker
@CircuitBreaker(name = "acquirerService", fallbackMethod = "fallback")
PaymentResponse process(PaymentRequest request);
```

**Execution flow:**
1. Request enters Retry boundary
2. Retry calls Feign method
3. Feign method enters Circuit Breaker boundary
4. If CB is OPEN, fallback executes immediately (no retry)
5. If CB is CLOSED and request fails, exception propagates to Retry
6. Retry attempts up to 3 times with exponential backoff
7. If all retries fail and CB hasn't tripped, final exception returns
8. If CB trips during retries, fallback executes for remaining attempts

### Load Amplification Factor Calculation

**Formula:**
```
L_f = (Total Requests Sent by V3) / (Total Requests Sent by V1)
```

**Example (Catastrophe Scenario):**
- V1: 45,000 requests sent (all unique from k6)
- V3: 45,000 initial + retries
  - Failed requests: ~60% (27,000)
  - Each failed request triggers 2 additional retries
  - Additional requests: 27,000 × 2 = 54,000
  - Total: 45,000 + 54,000 = 99,000
- L_f = 99,000 / 45,000 = 2.2

**In practice:** k6's request rate limiting prevented full amplification in our experiments, but production systems without backpressure mechanisms could see 3× amplification.

### Statistical Analysis Details

**Mann-Whitney U Test:**
- Non-parametric test comparing two independent samples
- Null hypothesis: V1 and V2 distributions are identical
- Alternative hypothesis: V2 latencies are systematically lower
- Result: U-statistic = XXX, p < 0.0001
- Conclusion: Reject null hypothesis at α = 0.01 significance level

**Cliff's Delta:**
- Non-parametric effect size measure ranging from -1 to +1
- Formula: `δ = (# pairs where V2 < V1 - # pairs where V2 > V1) / (n1 × n2)`
- Interpretation:
  - |δ| < 0.147: negligible
  - 0.147 ≤ |δ| < 0.33: small
  - 0.33 ≤ |δ| < 0.474: medium
  - |δ| ≥ 0.474: large
- Result: δ = 0.500 (large effect)

**95% Confidence Interval:**
- Bootstrap resampling with 10,000 iterations
- Lower bound: 823.42 ms reduction
- Upper bound: 863.95 ms reduction
- Mean: 843.77 ms reduction

---

## Presentation Tips

### Body Language
- **Posture:** Stand upright, shoulders back, weight evenly distributed
- **Hands:** Use natural gestures to emphasize points; avoid pockets or fidgeting
- **Eye Contact:** Rotate attention among committee members; don't fixate on one person or the screen
- **Movement:** Minimal pacing; plant yourself when delivering key points
- **Confidence:** Speak clearly, avoid filler words ("um," "uh," "like")

### Voice Control
- **Pace:** Moderate speed; slow down for complex concepts
- **Volume:** Loud enough for back row; project from diaphragm
- **Inflection:** Vary tone to maintain interest; emphasize key numbers and findings
- **Pauses:** Strategic silence after important points allows absorption

### Slide Interaction
- **Pointing:** Use a pointer or hand gesture to direct attention
- **Reading:** Never read slides verbatim; add value with additional context
- **Transitions:** Bridge between slides: "Now that we've seen X, let's examine Y"
- **Backup:** If projector fails, be prepared to present without slides

### Timing Management
- **Practice:** Rehearse full presentation multiple times; aim for 23-24 minutes to leave buffer
- **Milestones:** Check time at key transitions (Introduction at 6 min, Methodology at 11 min, Results at 21 min)
- **Flexibility:** If running long, skip backup slides or condense discussion section
- **Never rush:** Better to cut content than speak too fast

### Handling Questions
- **Listen fully:** Don't interrupt; let questioner finish completely
- **Pause before answering:** 2-3 second pause shows thoughtfulness
- **Clarify if needed:** "Just to ensure I understand, are you asking about...?"
- **Be honest:** If you don't know, say "That's an excellent question. I don't have data on that specific aspect, but I hypothesize..."
- **Bridge back:** Connect answers to your core findings
- **Thank questioners:** "Thank you for that insightful question."

### Technical Difficulties
- **Projector failure:** Continue verbally; describe key results from memory
- **Pointer failure:** Use hand gestures or verbal descriptions ("top-left corner")
- **Time shortage:** Prioritize results and conclusion; methodology can be condensed
- **Tough question:** "That's a complex issue. Let me address the core aspect..."

### Confidence Builders
- **You are the expert:** You know this work better than anyone in the room
- **Committee wants you to succeed:** They're evaluating quality, not trying to trip you up
- **Data speaks for itself:** Your results are strong; present them clearly
- **Preparation pays off:** Rehearsal reduces anxiety and improves delivery

---

## Final Checklist

**24 Hours Before:**
- [ ] Rehearse full presentation 3× times
- [ ] Test slides on presentation computer
- [ ] Prepare backup PDF (in case LaTeX fails)
- [ ] Review anticipated questions
- [ ] Print slide notes (backup if projector fails)
- [ ] Get good sleep (8 hours)

**1 Hour Before:**
- [ ] Arrive early; test equipment
- [ ] Set up laptop and projector
- [ ] Test slide advance clicker
- [ ] Check audio (if videos are included)
- [ ] Use restroom
- [ ] Deep breathing exercises

**During Presentation:**
- [ ] Start with confident introduction
- [ ] Make eye contact with committee
- [ ] Use pointer to guide attention
- [ ] Monitor time at milestones
- [ ] Pause after key findings
- [ ] Stay calm during questions
- [ ] Thank committee at conclusion

---

## Conclusion

**Remember:** Your research is strong. You have robust empirical evidence, rigorous statistical validation, and practical recommendations. Present with confidence, speak clearly, and let the data tell the story. The Circuit Breaker pattern **works**, and your thesis proves it quantitatively.

**Good luck!** You've got this. 🎓

---

## Additional Resources

### Recommended Reading Before Defense
- Michael Nygard, "Release It! 2nd Edition" (Chapter on Circuit Breakers)
- Martin Fowler's Circuit Breaker blog post
- RFC 9110 (HTTP Semantics) - Section on HTTP 202
- Netflix Tech Blog - Hystrix architecture

### Tools for Practice
- Record yourself presenting (phone video)
- Present to a friend or colleague
- Time each section individually
- Practice Q&A with advisor

### Mindset
> "The defense is not a test of what you don't know—it's a showcase of what you **do** know. You've spent months/years on this work. Trust your preparation, trust your data, and trust yourself."

**You are ready.**
