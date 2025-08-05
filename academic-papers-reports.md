

# **A Modular, AI-Driven Framework for the Autonomous Identification and Retrieval of Open Access Scholarly Literature**

## **Section 1: A Modular Framework for Autonomous Scholarly Retrieval**

The development of an autonomous agent capable of navigating the vast and heterogeneous landscape of the web to identify and retrieve scholarly literature necessitates an architectural foundation that is robust, scalable, and maintainable. A monolithic design, while potentially simpler to prototype, is ill-suited for the inherent unpredictability of web-based data extraction. Websites change their structure, APIs experience downtime, and network conditions fluctuate. A simple linear workflow proves brittle in the face of such web-scale heterogeneity. A more resilient architectural paradigm is a state-driven model, which allows for targeted retries, fault isolation, and more efficient resource allocation. This section outlines such a framework, presenting a multi-stage processing pipeline where each module represents a distinct state in the lifecycle of a URL's analysis.

### **1.1 System Architecture Overview: A Multi-Stage, State-Driven Processing Pipeline**

The proposed system architecture is a modular pipeline where the output of each stage serves as the input for the next. This design is informed by established principles in information retrieval and large-scale web scraping, which emphasize modularity for fault isolation, independent scalability, and ease of maintenance.1 An error in one module, such as a failure to download a PDF, will not halt the processing of other URLs in different stages, such as metadata extraction. Furthermore, individual modules can be scaled independently; for instance, the resource-intensive retrieval module can be allocated more concurrent workers than the lightweight triage module.

At the core of this architecture is a central data object, typically a JSON structure, which represents the state of each URL being processed. This object is progressively enriched as it passes through the pipeline. It begins with just a URL and is augmented with content type, metadata, open access (OA) status, a link to the full-text PDF, and a final status flag (e.g., SUCCESS, FAILURE\_PAYWALL, FAILURE\_NOT\_FOUND).

This pipeline is best conceptualized not as a rigid sequence but as a state machine. A URL transitions through a series of states: NEW, TRIAGED, CLASSIFIED\_AS\_PAPER, METADATA\_EXTRACTED, OA\_STATUS\_VERIFIED, RETRIEVAL\_PENDING, and finally COMPLETED or FAILED. This state-driven model provides significant advantages. A URL that fails during OA status verification due to a temporary API outage can be moved to a RETRY\_OA\_CHECK state and re-queued for later processing, rather than being discarded. This approach enables targeted retries, sophisticated error handling, and efficient parallel processing, transforming the agent from a simple script into a production-grade data processing system.4

### **1.2 Module 1: URL Ingestion and Content Triage**

The entry point for the system is the URL Ingestion and Content Triage module. Its primary function is to accept a heterogeneous list of resource URLs and perform a rapid, low-cost initial assessment to filter out obviously irrelevant links before they consume more significant computational resources.

This module begins by performing basic URL validation and normalization. It then executes a lightweight HTTP HEAD request using a library like Python's requests. This initial request retrieves the response headers without downloading the entire page content, providing crucial preliminary information. The Content-Type header is inspected to immediately discard non-HTML resources, such as direct links to images (image/jpeg), videos (video/mp4), or other binary files.

Following the header check, the module applies a set of heuristic rules based on URL structure. Regular expressions are used to identify patterns that strongly suggest a link to a scholarly article. URLs containing domains like arxiv.org, biorxiv.org, or doi.org, or path segments such as /abs/, /eprint/, or /pdf/, are prioritized and fast-tracked to the next module. Conversely, URLs with file extensions like .zip or .tar.gz are flagged as likely non-scholarly and can be deprioritized or discarded. This initial triage acts as a coarse but highly efficient filter, ensuring that the more computationally expensive analysis modules are reserved for URLs with a higher probability of being relevant.

### **1.3 Module 2: Scholarly Content Identification and Metadata Extraction**

This module serves as the intellectual core of the agent, tasked with two critical functions: definitively classifying a given URL as pointing to a scholarly research paper and, if so, extracting its essential bibliographic metadata. This process is necessarily multi-layered, combining static page analysis with advanced AI-driven techniques to handle the diversity of web content.

For URLs that pass the initial triage, this module first fetches the full page content. A crucial architectural decision at this stage is the choice of fetching mechanism. For many academic repositories and journal pages with simple, server-rendered HTML, a standard HTTP GET request via the requests library followed by parsing with BeautifulSoup is sufficient and efficient.5 However, a significant and growing number of publisher platforms rely on JavaScript to dynamically render content, including titles, author lists, and download links. For these cases, the module must escalate to a full browser automation framework like Playwright, which can execute the JavaScript and provide the fully rendered HTML Document Object Model (DOM) for analysis.6

Once the content is obtained, the dual process of classification and extraction begins. This involves a cascade of techniques, from heuristic pattern matching to sophisticated LLM-powered analysis, which will be detailed in Section 2\. The primary output of this module is a structured determination: either the URL is not a paper, or it is a paper, in which case a rich metadata object containing identifiers like a Digital Object Identifier (DOI) is passed to the next stage of the pipeline.

### **1.4 Module 3: Open Access Status Verification**

Upon receiving a validated scholarly paper with its associated metadata from Module 2, the Open Access Status Verification module takes over. Its sole responsibility is to determine the legal accessibility of the paper's full text. This is a critical step that ensures the agent operates within the bounds of copyright and publisher agreements.

This module functions primarily as an API client, orchestrating calls to a suite of specialized external services that maintain comprehensive databases of scholarly literature and their OA status. The primary identifier used for these queries is the DOI, which serves as a universal key for looking up a publication's record.

The module's logic is designed to be both efficient and resilient. It prioritizes the most reliable and specialized API for OA status determination while having fallback mechanisms to enrich the data or handle cases where the primary service is unavailable. The core technologies for this module are robust Python API client libraries such as unpywall for the Unpaywall API and habanero for the Crossref API.8 These libraries abstract away the complexities of HTTP requests, authentication, and response parsing, allowing the module's logic to focus on the strategy of querying and interpreting the results. The detailed comparison of these APIs and the recommended hybrid strategy for verification are the focus of Section 3\.

### **1.5 Module 4: Conditional and Compliant PDF Retrieval**

The final action-oriented component of the pipeline is the Conditional and Compliant PDF Retrieval module. This module is activated only when Module 3 provides a high-confidence, legally permissible URL pointing to an open access version of the paper's full text. Its function is to navigate to this URL and successfully download the PDF file.

The technical challenges in this module are non-trivial. A given OA URL might be a direct link to a PDF file, in which case a simple requests call is sufficient. More commonly, however, the URL leads to a landing page where the user must click a specific button or link to initiate the download. These interactive elements are often rendered and managed by JavaScript, necessitating the use of a browser automation framework like Playwright.6 The agent must be capable of identifying and interacting with these elements to complete the retrieval process.

Crucially, this module operates under the strict governance of an integrated "Compliance Sub-module." This sub-module enforces the ethical and legal constraints detailed in Section 6\. It ensures that the agent respects robots.txt directives, adheres to self-imposed rate limits to avoid overwhelming the host server, and correctly identifies itself in the User-Agent string. This ensures that the retrieval process is not only technically successful but also responsible and compliant with community norms and legal frameworks.

## **Section 2: Intelligent Resource Identification with NLP and Large Language Models**

The efficacy of the entire framework hinges on the intelligence of Module 2: its ability to accurately distinguish scholarly articles from the web's vast expanse of other content types and to precisely extract the metadata required for subsequent processing. This section details a multi-layered strategy that combines fast, deterministic heuristics with the advanced contextual understanding of Natural Language Processing (NLP) and Large Language Models (LLMs) to achieve high precision and recall in this critical task.

### **2.1 Heuristic and Model-Based Classification of Web Content**

The classification process employs a cascading approach, starting with the fastest and cheapest methods and escalating to more computationally intensive techniques only when necessary. This creates a cost-performance hierarchy that optimizes resource usage.

The first layer consists of **heuristic-based classification**. This involves searching the fetched HTML for strong, unambiguous indicators of scholarly content. This includes checking for the presence of specific \<meta\> tags commonly used by academic publishers and indexing services, such as citation\_title, citation\_author, citation\_doi, and Dublin Core elements like DC.identifier. The presence of a structured "References" or "Bibliography" section in the HTML is another powerful heuristic.

If these heuristics are inconclusive, the agent escalates to **model-based classification**. The page's primary text content is extracted and passed to an AI model. Foundational NLP techniques like Named Entity Recognition (NER) can be applied to identify the density and type of entities present. A high prevalence of entities classified as persons (authors), organizations (universities, research labs), and domain-specific technical terms is a strong signal of a scholarly document.12

For the most ambiguous cases, the agent leverages an **LLM as a zero-shot classifier**. The extracted text is provided to a powerful LLM with a carefully crafted prompt, instructing it to classify the content into one of several predefined categories: 'Academic Research Paper', 'Blog Post', 'News Article', 'Software Repository', or 'Product Documentation'.15 The LLM's vast pre-trained knowledge allows it to discern subtle differences in structure, tone, and vocabulary that distinguish these content types, achieving high accuracy without the need for a custom-trained classification model.17

### **2.2 A Schema-Driven Approach to Metadata Extraction**

Once a URL has been confidently classified as a scholarly paper, the agent must extract its core metadata. Relying on fixed CSS selectors or regular expressions for this task is brittle and not scalable across the thousands of different journal and repository layouts. A far more robust and adaptable method is a schema-driven approach powered by an LLM, a technique pioneered by advanced information extraction frameworks like MOLE.19

This methodology centers on a predefined **JSON schema** that acts as a structured template for the LLM. This schema defines all the metadata fields the agent needs to extract, such as title, authors, doi, publication\_year, and abstract. Critically, each field in the schema is associated with several properties that guide the LLM's extraction process and enable subsequent validation 19:

* **question**: A clear, natural language prompt for the LLM (e.g., "What is the full title of this research paper?").  
* **answer\_type**: The expected data type for the extracted value (e.g., string, list\[string\], integer), which is essential for validation.  
* **options**: For fields with a constrained set of possible values (like license), this provides a list for the LLM to choose from.

The agent constructs a prompt containing the full text of the paper and the JSON schema, instructing the LLM to populate the schema based on the provided text.15 The LLM's ability to understand natural language allows it to locate the relevant information within the unstructured text and map it to the correct field in the schema.

The raw JSON output from the LLM is not trusted implicitly. It is passed through a rigorous **validation pipeline** to ensure data integrity, mirroring the design of the MOLE framework.20 This pipeline performs several checks:

1. **JSON Validation**: Ensures the entire output is a valid, parsable JSON object. Regular expressions are used to fix common LLM formatting errors, such as extraneous markdown fences (e.g., \`\`\`json... \`\`\`).  
2. **Type Validation**: Verifies that the data type of each extracted value matches the answer\_type specified in the schema. It can perform safe type casting where appropriate (e.g., converting a string "2023" to an integer).  
3. **Option Validation**: For fields with a predefined list of options, this step checks if the LLM's output is a valid choice. If not, it can use string similarity matching to correct for minor variations or typos.

This schema-driven extraction and validation process transforms the unstructured chaos of a web page into clean, reliable, and structured metadata.

### **2.3 Extracting and Validating Key Identifiers (DOI, arXiv ID)**

The single most important piece of metadata to extract is a persistent identifier, most commonly a DOI or an arXiv ID, as this is the key to querying the OA status APIs. Due to its criticality, a multi-layered extraction and validation strategy is employed, creating an "extraction cascade" that balances speed, cost, and accuracy. This layered approach is superior to relying on a single method, as it mitigates the primary weakness of each individual technique.

The cascade begins with the fastest and most reliable method: **regex-based extraction**. The agent scans the full HTML source and extracted text for patterns that match the known formats of DOIs (e.g., 10.\\d{4,9}/.+) and arXiv IDs. If a clear match is found, it is used as the primary candidate. This method is extremely fast and has a very low false positive rate when a match is found.

If the regex search fails, the agent escalates to the more powerful but computationally more expensive **LLM-based extraction** described in the previous section. The doi and arxiv\_id fields in the schema will prompt the LLM to find these identifiers, even if they are not presented in a standard format.

The final and most critical step is **cross-validation**. Regardless of whether the identifier was found via regex or an LLM, it must be validated against an external authority. For a DOI, the agent makes a simple API call to https://doi.org/{doi} or the Crossref API.24 A successful response that resolves to a valid metadata record confirms the DOI's authenticity. This step is crucial for preventing "hallucinated" identifiers that LLMs can sometimes generate, ensuring that only valid identifiers are passed to the next stage of the pipeline. This closed-loop validation significantly increases the overall reliability of the system.

## **Section 3: A Comparative Analysis of Scholarly Data APIs for OA Verification**

Once an academic paper has been identified and its DOI has been extracted and validated, the agent proceeds to Module 3: Open Access Status Verification. This module's effectiveness is entirely dependent on the quality, scope, and reliability of external scholarly data APIs. A naive implementation might rely on a single data source, but a robust agent must understand the intricate ecosystem of these services, their interdependencies, and their respective strengths and weaknesses. This section provides a deep comparative analysis of the three cornerstone APIs in this domain—Crossref, Unpaywall, and OpenAlex—and proposes a hybrid, fault-tolerant strategy for determining OA status with maximum accuracy.

### **3.1 The Central Role of Unpaywall, OpenAlex, and Crossref**

The open scholarly data landscape is powered by a few key players whose services are often layered on top of one another. Understanding this data supply chain is fundamental to designing an effective verification strategy.

* **Crossref:** As a primary Digital Object Identifier (DOI) Registration Agency, Crossref sits at the foundation of the ecosystem. Publishers deposit bibliographic metadata directly with Crossref when they register a DOI. Therefore, the Crossref REST API is the authoritative source for core, publisher-provided metadata, including titles, authors, publication dates, funding information, license details, and registered references.24 It is the ground truth for what a DOI represents.  
* **Unpaywall:** Operated by the non-profit OurResearch, Unpaywall is a specialized service built to solve one problem exceptionally well: determining the open access status of a scholarly article. It aggregates data from thousands of sources, including Crossref, PubMed Central, institutional repositories, and publisher websites, to find legally hosted open access copies.28 Its API provides a simple, direct answer to the question "Is this DOI available OA, and if so, where is the best version?" Unpaywall's clear definitions of OA "colors" have become the de facto industry standard, adopted by major platforms like Scopus.30  
* **OpenAlex:** Also a project from OurResearch, OpenAlex is a far more ambitious undertaking. It aims to create a fully open and comprehensive map of the entire global research system, indexing not just works but also authors, institutions, funders, and concepts, and charting the relationships between them.32 It is effectively a massive, interconnected knowledge graph. To achieve this scale, OpenAlex ingests data from multiple sources, including the now-defunct Microsoft Academic Graph (MAG), Crossref, and, critically for this agent's purpose, the complete Unpaywall dataset for its OA information.35

### **3.2 In-Depth API Comparison: Data, Rate Limits, and Access Models**

A successful agent must treat these APIs not as interchangeable but as specialized tools, each with a distinct purpose. The choice of which API to call, and in what order, has significant implications for data quality, efficiency, and cost. The following table provides a detailed, head-to-head comparison to inform this strategic decision.

This table is essential for the Technical Lead to make an informed decision on which API to prioritize for different tasks. It centralizes critical operational data (rate limits, data points, reliability) that is otherwise scattered across documentation pages. A developer needs to know the strengths, weaknesses, and costs (rate limits) of each to design an efficient system. Simply describing them is not enough; a side-by-side comparison is the most effective way to convey this information. The columns reflect the key decision-making criteria: What data can I get? How fast can I get it? What does it cost? How reliable is it? This structure directly supports the design of the hybrid strategy in section 3.3.

**Table 1: Comparative Analysis of Open Access APIs**

| Feature | Unpaywall API | OpenAlex API | Crossref REST API |
| :---- | :---- | :---- | :---- |
| **Primary Use Case** | Definitive OA status determination and retrieval of the best legal PDF link. | Exploration of the scholarly knowledge graph; finding connections between works, authors, and institutions. | Retrieval of authoritative, publisher-deposited bibliographic metadata for a DOI. |
| **Key Data Points** | oa\_status (gold, green, etc.), best\_oa\_location (with URL, license, version), is\_oa boolean. | referenced\_works, related\_works, author affiliations, concepts, funders, citation counts. OA data is inherited from Unpaywall. | Title, authors, abstract, publication date, journal, ISSN, funder information, license URLs, reference lists. |
| **Rate Limit (Public)** | 100,000 requests/day.29 | 100,000 requests/day.32 | 50 requests/second (in "polite pool").25 |
| **Authentication** | Free; requires an email address in the request parameter for optimal performance.29 | Free; requires an email address in a mailto parameter to join the "polite pool".32 | Free for public use; requires an email in the Mailto header to join the "polite pool".26 |
| **Data Source** | Harvests data from Crossref, DOAJ, PubMed, and over 50,000 repositories and publisher sites.28 | Integrates data from Unpaywall, MAG, Crossref, ORCID, and others to build its knowledge graph.36 | Primary data is deposited directly by publishers upon DOI registration.26 |
| **Known Issues/Nuances** | Considered the gold standard for OA status. Limited bibliographic data beyond what's needed for OA determination. | Research has identified significant inconsistencies between its is\_oa flag and oa\_status field, with millions of records potentially mislabeled.37 | Does not directly compute an OA "color." OA status must be inferred from the presence and type of license information, which may not always be available.26 |

The most critical takeaway from this analysis is the data lineage and its impact on quality. Since OpenAlex ingests its OA data from Unpaywall, Unpaywall should be considered the more direct and authoritative source for the specific task of OA status verification. Furthermore, documented inconsistencies in how OpenAlex processes and presents this data mean that relying solely on its is\_oa flag is risky.37 A robust agent must either prioritize Unpaywall or, if using OpenAlex, reimplement the Unpaywall classification logic based on the underlying

best\_oa\_location data object.

### **3.3 A Hybrid, Fault-Tolerant Strategy for OA Status Determination**

Based on the comparative analysis, a single-API strategy is fragile. The optimal approach is a hybrid, fault-tolerant workflow that leverages the strengths of each service in a prioritized cascade:

1. **Primary Query to Unpaywall:** For any given DOI, the agent's first action is to query the Unpaywall API. This provides the most accurate oa\_status and, most importantly, the best\_oa\_location object, which contains the direct URL to the best available legal copy of the full text.29 This is the fastest path to a successful retrieval.  
2. **Enrichment and Fallback with OpenAlex/Crossref:** If Unpaywall returns a result, the agent can optionally query OpenAlex or Crossref with the same DOI to enrich its metadata object with additional information not present in Unpaywall, such as the full abstract, author affiliations, or citation counts. If Unpaywall returns no result for a valid DOI (a rare but possible occurrence), the agent should then query OpenAlex as a fallback. However, if it relies on OpenAlex for OA status, it must use the reclassification logic derived from Unpaywall's methodology: check for the existence of a best\_oa\_location object, rather than trusting the top-level is\_oa boolean, to determine accessibility.37  
3. **Handling Non-DOI Sources:** The agent must possess specialized logic for repositories that do not primarily use DOIs but are inherently open. The most prominent example is ArXiv. The agent should include a rule-based system that identifies ArXiv URLs (e.g., arxiv.org/abs/...). For these, it can bypass the API verification step entirely, classify the paper as green OA, and construct the PDF download URL directly (e.g., by replacing /abs/ with /pdf/). This avoids unnecessary API calls and handles a significant portion of the preprint literature efficiently.

This hybrid strategy maximizes accuracy by prioritizing the most specialized tool (Unpaywall), enhances data richness by leveraging comprehensive graphs (OpenAlex/Crossref), and improves efficiency by hard-coding logic for known-open sources.

## **Section 4: Advanced Agent Capabilities through Generative AI**

While the modules described thus far can create a functional agent, leveraging the reasoning and generation capabilities of modern Large Language Models (LLMs) can elevate it from a rigid, rule-based system to a resilient, adaptive agent. Traditional web scrapers are notoriously brittle; they break when a website's developers change a CSS class or restructure the HTML. LLMs offer a paradigm shift, allowing the agent to operate based on a high-level *goal* (e.g., "find the PDF download link") rather than a low-level, hard-coded *instruction* (e.g., "click the element with id='pdf-download-button'"). This section explores two advanced applications of LLMs that directly address the most common and difficult challenges in automated web retrieval.

### **4.1 LLM-Powered Navigation for Dynamic and Complex Publisher Websites**

The final step of retrieving a PDF is often the most challenging. While Unpaywall may provide a URL to an OA landing page, that page frequently does not link directly to the PDF file. Instead, the user must interact with JavaScript-rendered buttons, accept terms and conditions, or navigate a multi-step download process. This dynamic environment is the primary failure point for scrapers built with simple tools like requests and BeautifulSoup.

To overcome this, the agent can employ an LLM as a dynamic navigation engine, a concept explored in recent research on autonomous web agents.39 The workflow operates as an iterative loop of observation, reasoning, and action:

1. **Observation:** The agent uses a browser automation framework like Playwright to navigate to the target URL and render the complete page, including all JavaScript-driven elements. It then extracts a simplified representation of the page's DOM, focusing on interactive elements like \<a\>, \<button\>, and \<input\>, along with their text content and key attributes.  
2. **Reasoning:** This simplified DOM, along with the high-level objective ("Find and click the link to download the full-text PDF of the article"), is passed to an LLM. The LLM acts as a reasoning engine. It analyzes the context of the interactive elements and determines the most logical next step. For example, it might identify a button with the text "Download PDF" or "Full Text (PDF)" as the most promising target.  
3. **Action Generation:** The LLM's output is not just a decision but a specific, executable action. For example, it might return a JSON object like {"action": "click", "selector": "a.pdf-download-link"}.  
4. **Execution:** The agent parses this response and uses Playwright to execute the specified action (e.g., page.click("a.pdf-download-link")).

This loop repeats. After the click, the agent observes the new page state (e.g., a new tab opens with the PDF, or a new modal appears) and feeds this back to the LLM for the next decision. This approach, particularly when structured with an explore-critic paradigm where one part of the model proposes actions and another evaluates progress, allows the agent to reason its way through complex, multi-step interactions that would be nearly impossible to hard-code.42 This decouples the agent's logic from the website's specific implementation, creating a system that is resilient to the constant churn of web design.

### **4.2 Classifying Paywalls and Access Barriers for Strategic Retrieval**

When the agent lands on a page that is not immediately identifiable as an open access article, it faces an access barrier. Not all barriers are equal; a hard paywall is a definitive dead end, while a registration wall or a CAPTCHA challenge might be navigable under certain conditions. The agent needs to intelligently classify these barriers to make a strategic decision about whether to proceed or abort.

Here, an LLM can be employed as a powerful, context-aware classifier. The agent can provide the full text of the landing page to an LLM with a prompt designed for few-shot classification.16 The prompt would define the possible categories and might include brief examples of each:

"Analyze the following web page content. Classify the access barrier for the full-text article as one of: 'Hard Paywall' (requires a paid subscription), 'Institutional Login' (requires university or corporate credentials), 'Registration Wall' (requires a free account), 'Metered Paywall' (offers a limited number of free articles), or 'No Barrier Detected'. Provide the classification and a brief justification."

The LLM's classification directly informs the agent's strategy:

* **Hard Paywall or Institutional Login**: The agent immediately aborts the retrieval attempt for this URL. This confirms the paper is not legally OA through this route and prevents the agent from wasting resources.  
* **Registration Wall**: The agent aborts for now but can log this URL for a potential future enhancement where the agent could manage disposable accounts for such sites.  
* **No Barrier Detected**: This signals that the page is likely an OA landing page, and the agent should initiate the LLM-powered navigation workflow from Section 4.1 to find the download link.

While some research has explored using LLMs to generate JavaScript to actively *bypass* client-side paywalls 44, this agent's design uses classification for strategic

*avoidance*, ensuring its operations remain squarely within ethical and legal boundaries. This intelligent classification of access barriers is a key feature that distinguishes a sophisticated agent from a simple scraper.

## **Section 5: Implementation Blueprint and Foundational Technologies**

The successful implementation of the proposed framework depends on the judicious selection of a robust and well-supported technology stack. The Python ecosystem offers a mature and comprehensive suite of libraries perfectly suited for every module of the agent, from low-level HTTP requests to advanced browser automation and data manipulation. This section provides a detailed blueprint for the agent's implementation, justifying the choice of key libraries and frameworks.

### **5.1 Core Python Ecosystem for Web Scraping and Data Handling**

The foundation of the agent's non-interactive web operations will be built upon a trio of industry-standard Python libraries.

* **HTTP Requests with requests:** For all direct interactions with APIs (Crossref, Unpaywall, OpenAlex) and for the initial, lightweight fetching of static HTML content in the Triage module, the requests library is the unequivocal choice. Its simple, elegant API, robust session management, and comprehensive handling of HTTP protocols make it the standard for any Python application involving web requests.5  
* **HTML/XML Parsing with BeautifulSoup:** Once static HTML content is retrieved, it must be parsed into a navigable structure. BeautifulSoup is the ideal library for this task. It excels at handling imperfect or "tag soup" HTML, which is common on the web, and provides a highly intuitive, Pythonic interface for searching and manipulating the parse tree.5 It will be used extensively in Module 2 for heuristic-based classification and initial metadata extraction from simple web pages.  
* **Data Manipulation with pandas:** As the agent processes URLs and enriches them with data, it needs a powerful way to manage this information. The pandas library, with its core DataFrame structure, is perfectly suited for this. API responses, especially from batch queries, can be naturally loaded into DataFrames for efficient filtering, transformation, and storage. The utility of this approach is demonstrated by the unpywall library, which returns its results directly as a pandas DataFrame, streamlining the data handling workflow.10

### **5.2 Selecting a Browser Automation Framework: Selenium vs. Playwright**

For any task involving interaction with dynamic, JavaScript-heavy websites—a necessity for Module 4 (PDF Retrieval) and for handling complex publisher portals—a full browser automation framework is required. The two leading contenders in the Python ecosystem are Selenium and Playwright. While Selenium is the more established tool, a detailed comparison reveals that Playwright's modern architecture and design philosophy make it the superior choice for this agent.

The decision to recommend Playwright is based on its direct solutions to the most common failure points in automated web scraping: speed and reliability. An autonomous agent that must process thousands of URLs cannot be hindered by flaky tests or slow execution. Playwright's architectural advantages translate directly into a more robust and efficient agent. The following table provides a clear, evidence-based justification for this critical architectural decision, allowing a technical lead to quickly grasp the trade-offs and understand why the modern tool is better suited for this specific task.

**Table 2: Comparison of Browser Automation Frameworks**

| Feature | Selenium | Playwright | Recommendation for Agent |
| :---- | :---- | :---- | :---- |
| **Architecture** | Uses the WebDriver API, which communicates with the browser via the HTTP protocol for each command.6 | Uses a persistent WebSocket connection via the Chrome DevTools Protocol (or equivalents for other browsers).6 | **Playwright.** The persistent connection significantly reduces the overhead of repeated HTTP handshakes, leading to faster and more reliable command execution. |
| **Execution Speed** | Generally slower due to the command-by-command HTTP request/response cycle.6 | Markedly faster due to its modern architecture and reduced communication overhead.6 | **Playwright.** For a high-throughput agent processing a large volume of URLs, execution speed is a critical performance metric. |
| **Handling Dynamic Content** | Relies on developers implementing explicit and implicit waits (e.g., WebDriverWait). Improperly configured waits are a primary source of "flaky" tests that fail intermittently.6 | Features built-in "auto-wait" mechanisms. Before performing an action like a click, Playwright automatically waits for the element to be visible, stable, and actionable, dramatically increasing script reliability.7 | **Playwright.** The auto-wait feature is a transformative advantage for an autonomous agent. It makes the scripts far more resilient to variations in page load times and asynchronous content rendering, which are common on publisher websites. |
| **API Design** | Primarily offers a synchronous API. Asynchronous operations can be complex to manage. | Provides both synchronous and asynchronous (async/await) APIs out of the box, making it ideal for modern, I/O-bound applications.51 | **Playwright.** The native async API allows for more efficient handling of concurrent browser operations, enabling the agent to be built on a more scalable and performant foundation. |
| **Setup and Dependencies** | Requires manual management of separate WebDriver executables (e.g., chromedriver.exe) for each browser, which must be kept in sync with the browser version.6 | Manages its own browser binaries through a simple command-line interface (playwright install). This ensures that the library and the browsers it controls are always compatible.51 | **Playwright.** The simplified setup and dependency management reduce maintenance overhead and deployment complexity. |

### **5.3 Leveraging Specialized Python Clients for Scholarly APIs**

While it is possible to interact with the scholarly APIs directly using requests, a more efficient and maintainable approach is to use existing, well-supported client libraries. These libraries handle the nuances of authentication, pagination, error handling, and response parsing, allowing the agent's code to focus on its core logic.

* For Unpaywall: unpywall  
  This library is the ideal choice for interacting with the Unpaywall API. It is a dedicated client that simplifies authentication, provides straightforward methods for querying by DOI or text, and conveniently returns results as a pandas DataFrame.8 Its functions for directly retrieving PDF links (  
  get\_pdf\_link) and other document links (get\_doc\_link) are perfectly aligned with the agent's goals.  
* For Crossref: habanero  
  habanero is a robust, low-level client for the Crossref API. It provides a clean, one-to-one mapping of its methods to the Crossref API routes (e.g., cr.works(), cr.funders()), giving the agent full access to the rich bibliographic data available through the service.9 It is the perfect tool for the validation and data enrichment steps in Module 3\.  
* For OpenAlex:  
  The OpenAlex documentation lists several third-party Python libraries, including PyAlex and OpenAlexAPI.34 The agent should adopt one of these libraries to standardize its interactions with the OpenAlex API, particularly for handling complex filtering and pagination when exploring the scholarly graph.

By building upon these specialized libraries, the agent's development can be significantly accelerated, and its codebase will be more robust and easier to maintain.

## **Section 6: Navigating the Technical and Ethical Landscape of Automated Retrieval**

An autonomous agent operating at scale on the public web does not exist in a vacuum. It must contend with a sophisticated and ever-evolving landscape of technical defenses designed to thwart automation, and it must operate within a complex framework of legal and ethical norms. A successful agent is therefore not just technically proficient but also a responsible and "polite" digital citizen. This section details the dual challenges of overcoming anti-scraping mechanisms and adhering to a strict ethical and legal protocol. These two aspects are deeply intertwined; often, the most ethical approach is also the most effective at avoiding detection.

### **6.1 Advanced Anti-Scraping Techniques and Evasion Strategies**

Web scraping exists in an adversarial dynamic. As scrapers become more sophisticated, so do the anti-scraping technologies deployed by websites to protect their data and server resources.62 The agent must be designed from the ground up with a multi-layered defense strategy to counter these measures. The following table serves as a practical guide for developers, outlining the primary threats and the corresponding countermeasures the agent must implement.

**Table 3: Common Anti-Scraping Techniques and Agent Countermeasures**

| Anti-Scraping Technique | Description | Agent Countermeasure(s) | Recommended Libraries/Services |
| :---- | :---- | :---- | :---- |
| **IP-Based Rate Limiting & Blocking** | Servers monitor the number of requests from a single IP address and will block or throttle IPs that exceed a certain threshold. This is the most common anti-bot measure.62 | Use a large pool of high-quality, rotating residential or mobile proxy IPs. Each request should appear to come from a different, legitimate user, distributing the load and making it difficult to identify the agent's activity based on its IP address.4 | Commercial proxy providers (e.g., Bright Data, Oxylabs, NetNut).62 |
| **User-Agent & HTTP Header Validation** | Servers inspect the User-Agent string and other HTTP headers to filter out requests that do not originate from a standard web browser. Default user-agents from libraries like requests are easily blocked.64 | Maintain and rotate a list of User-Agent strings from real, modern web browsers. Ensure that other headers (e.g., Accept-Language, Referer) are also present and consistent with a real browser session.66 | Libraries like fake-useragent for Python; custom header management within requests or Playwright. |
| **Browser Fingerprinting** | Advanced systems execute JavaScript on the client to collect a unique "fingerprint" based on attributes like screen resolution, installed fonts, plugins, and canvas rendering. This can reliably distinguish a real user's browser from a standard automation environment.64 | Use a fortified headless browser that is specifically designed to evade detection. This involves modifying the JavaScript environment to remove automation-specific properties (e.g., navigator.webdriver). | Playwright with stealth plugins or custom configurations. The undetected-chromedriver project provides this functionality for Selenium.67 |
| **CAPTCHA Challenges** | "Completely Automated Public Turing test to tell Computers and Humans Apart." These challenges (e.g., distorted text, image selection) are explicitly designed to block bots.69 | The agent must first be able to detect a CAPTCHA. Upon detection, it should not attempt to solve it directly but instead pass the challenge to a third-party, human-powered CAPTCHA-solving service via their API.66 | API-based services like 2Captcha or Anti-Captcha.66 |
| **Honeypots** | Websites may include links or form fields that are invisible to human users (e.g., via display: none; in CSS) but are present in the HTML. These act as traps; any interaction with them immediately flags the visitor as a bot.62 | The agent's navigation logic must be configured to interact only with elements that are visible and actionable by a human user. Browser automation frameworks like Playwright provide methods to check for element visibility before interaction. | Playwright's visibility checks (e.g., is\_visible()). |
| **Behavioral Analysis** | Sophisticated systems track user behavior over time, analyzing mouse movements, scrolling speed, and click patterns. Non-human, perfectly linear, and instantaneous actions are a clear sign of automation.63 | When using a browser automation framework, the agent should introduce randomized delays and mimic human-like interaction patterns. This includes moving the mouse cursor over elements before clicking and adding small, variable pauses between actions.66 | Playwright's ActionChains or similar features to simulate complex user gestures. |

### **6.2 A Framework for Ethical and Legally Compliant Operation**

Beyond technical evasion, the agent must operate under a strict ethical and legal framework to ensure its long-term viability and to act as a responsible participant in the web ecosystem. Ethical compliance is not merely a constraint but a core component of the agent's operational strategy; a "polite" agent is less likely to trigger aggressive anti-scraping defenses.

1. **Respect robots.txt:** The robots.txt file is a web standard that allows site administrators to specify which parts of their site should not be accessed by automated agents. The agent must, as its first action upon interacting with a new domain, fetch and parse this file. It must strictly adhere to all Disallow directives for its user-agent string.71  
2. **Adhere to Terms of Service (ToS):** The legal landscape regarding scraping in violation of a website's ToS is complex. However, from an ethical standpoint, the agent should avoid scraping data from websites that explicitly prohibit automated access in their ToS.72 While parsing the full legal text of a ToS for every site is impractical, the agent can be programmed to avoid domains that are known to have restrictive policies.  
3. **Implement Aggressive Throttling and Polite Pacing:** To avoid placing an undue burden on web servers, the agent must be designed to be "patient." This involves implementing several mechanisms:  
   * **Conservative Rate Limiting:** A global rate limit should be set to a low number of requests per second per domain.  
   * **Randomized Delays:** A random delay should be introduced between consecutive requests to the same domain to mimic human browsing patterns.71  
   * **Exponential Backoff:** If the agent receives an error response from a server (e.g., HTTP 429 "Too Many Requests" or 503 "Service Unavailable"), it must not immediately retry. Instead, it should implement an exponential backoff algorithm, progressively increasing the wait time between retry attempts.71  
4. **Transparent Identification:** The agent should not attempt to hide its identity. Its User-Agent string should be truthful, identifying it as an automated research agent and, where possible, providing a URL that links to a page describing the project's purpose and contact information. This transparency allows web administrators to understand the agent's activity and provides a channel for communication.71  
5. **Operate within Legal Precedents:** The agent's design is informed by key legal rulings. The landmark U.S. case *hiQ Labs, Inc. v. LinkedIn Corp.* established that scraping publicly accessible data (i.e., data not behind a login wall) does not violate the Computer Fraud and Abuse Act (CFAA).73 This provides a legal foundation for the agent's core mission. However, this precedent also reinforces a critical boundary: the agent must  
   **never** attempt to access data that requires authentication, bypass login walls, or otherwise breach technical access controls, as this would likely constitute "unauthorized access" under the CFAA.74  
6. **Ensure Data Privacy:** While the agent's target is published research, it must be designed to scrupulously avoid the collection of any Personally Identifiable Information (PII). It should not scrape comment sections, user profiles, or other areas where PII might be present. All data processing should be designed with the principle of data minimization in mind, collecting only the bibliographic metadata necessary for the task.71

By integrating these technical and ethical principles into its core design, the agent can achieve its objectives while minimizing its disruptive footprint and operating on a sound legal and ethical foundation.

## **Section 7: A Robust Framework for Performance Evaluation**

Evaluating the performance of a complex, multi-stage AI agent requires a nuanced approach. A single, monolithic "accuracy" score is insufficient and can be misleading. The system's performance must be assessed at each stage of its pipeline, using a combination of traditional, quantitative information retrieval metrics for its deterministic components and more qualitative, human-in-the-loop methods for its generative AI-driven modules. This hybrid evaluation framework allows for targeted debugging, identifies specific bottlenecks, and provides a holistic understanding of the agent's real-world effectiveness.

### **7.1 Quantitative Metrics for Identification and Retrieval Success**

To quantitatively measure the agent's performance, a ground-truth dataset must be established. This dataset should consist of a diverse list of several hundred URLs, manually annotated with the following information: (a) whether the URL points to a scholarly paper, (b) the paper's correct DOI (if applicable), and (c) its true open access status and the location of a legal OA PDF (if one exists). Against this benchmark, the following metrics can be calculated:

* **Identification Precision and Recall:** These are foundational metrics for evaluating the classification performance of Module 2\.76  
  * **Precision:** Of all the URLs the agent classified as being a scholarly paper, what percentage were correct? This is calculated as Precision=TP+FPTP​, where TP (True Positives) is the number of papers correctly identified and FP (False Positives) is the number of non-papers incorrectly identified as papers. High precision indicates the agent is not polluting its results with irrelevant content.  
  * **Recall:** Of all the URLs in the dataset that were actually scholarly papers, what percentage did the agent successfully identify? This is calculated as Recall=TP+FNTP​, where FN (False Negatives) is the number of papers the agent failed to identify. High recall indicates the agent is comprehensive in its search.  
  * **F1 Score:** The harmonic mean of precision and recall, calculated as F1=2×Precision+RecallPrecision×Recall​, provides a single, balanced measure of classification accuracy.  
* **OA Status Accuracy:** For the set of correctly identified papers (the True Positives from the previous step), this metric measures the accuracy of Module 3\. It is the percentage of papers for which the agent correctly determined the OA status (e.g., gold, green, closed).  
* **Retrieval Precision and Recall (Success Rate):** These metrics evaluate the end-to-end performance of the entire pipeline.  
  * **Retrieval Precision:** Of all the PDF files the agent successfully downloaded, what percentage were the correct paper and genuinely open access? This guards against the agent downloading incorrect files or paywalled content.  
  * **Retrieval Recall:** Of all the papers in the ground-truth dataset that were annotated as having a legally available OA PDF, what percentage did the agent successfully retrieve? This is the ultimate measure of the agent's effectiveness in achieving its primary goal.

### **7.2 Qualitative and Nuanced Evaluation of LLM-Driven Components**

The generative and reasoning-based components of the agent, particularly the LLM-powered navigation and classification modules, cannot be fully evaluated with simple quantitative scores. The generative nature of their outputs makes automatic evaluation difficult and can lead to misleading metrics, a known challenge in the evaluation of LLM-based data extraction systems.77 Therefore, a qualitative, human-in-the-loop evaluation process is essential.

* **Navigation Logic Evaluation:** For every instance where the agent uses the LLM for web navigation (Section 4.1), it must log the entire decision-making process. This includes the simplified DOM provided to the LLM, the LLM's "thought" process (if available through chain-of-thought prompting), and the final action it recommended. Human reviewers would then assess these logs, answering questions such as: Was the LLM's interpretation of the page logical? Was the chosen action the most sensible next step? How did the agent recover from an incorrect action? This provides deep insight into the robustness and reasoning capabilities of the navigation module.  
* **Metadata Extraction Evaluation:** While a simple correct/incorrect score can be used for metadata like the DOI, fields containing natural language (e.g., title, abstract) require a more nuanced evaluation. For these, standard NLP metrics like token-level F1 scores can be calculated against the ground-truth extraction to measure the degree of overlap and accuracy.77 This distinguishes between a completely wrong extraction and one that has minor phrasing differences.  
* **Comprehensive Error Analysis:** A critical component of the evaluation framework is a systematic analysis of every failure. For each URL that the agent failed to process correctly, the reason for the failure must be categorized. Did it fail at triage? Was it misclassified? Was the DOI extracted incorrectly? Did the OA status check timeout? Was the PDF download button not found? This detailed error analysis is the most valuable source of information for iterative improvement, allowing developers to pinpoint and address the weakest links in the processing chain.

By combining these quantitative pipeline metrics with qualitative analysis of the AI components, a comprehensive and actionable picture of the agent's performance can be achieved.

## **Section 8: Conclusion and Future Directions**

This report has detailed the architectural blueprint for a modular, AI-driven autonomous agent designed for the specific and challenging task of identifying and retrieving open access scholarly literature from the web. The proposed framework is built upon a foundation of robust, state-of-the-art technologies and a deep understanding of the scholarly communication ecosystem.

### **8.1 Summary of Design**

The core design principles of the agent are rooted in resilience, intelligence, and ethical operation.

* **A Modular, State-Driven Architecture:** The agent is structured as a multi-stage pipeline, allowing for fault tolerance, scalability, and maintainability. By treating the workflow as a state machine, the system can gracefully handle the inherent unpredictability of web-based data extraction.  
* **A Hybrid, Cascade-Based Intelligence:** The agent employs a cascade of techniques for classification and extraction, beginning with fast, low-cost heuristics and escalating to powerful but resource-intensive LLMs only when necessary. This tiered approach optimizes for both speed and accuracy. The schema-driven metadata extraction, inspired by the MOLE framework, ensures that the unstructured data of the web is transformed into clean, validated, and structured information.  
* **Strategic Use of Generative AI:** The agent moves beyond simple parsing by leveraging LLMs for advanced reasoning tasks. An LLM-powered navigation engine provides resilience against changing website layouts, while an LLM-based classifier allows for intelligent, strategic decisions when encountering access barriers like paywalls.  
* **A Multi-Source, Fault-Tolerant Verification Strategy:** The agent does not rely on a single source of truth for open access status. It uses a hybrid strategy that prioritizes the specialized Unpaywall API, enriches data with the comprehensive graphs of OpenAlex and Crossref, and includes fallback and reclassification logic to ensure maximum reliability.  
* **A Foundational Commitment to Ethical and Compliant Operation:** The agent is designed to be a good digital citizen. Its operation is governed by a strict protocol that includes respecting robots.txt and Terms of Service, aggressive rate-limiting to protect server resources, and transparent identification. This ethical framework is not merely a constraint but a core component of its strategy to avoid detection and ensure long-term operational viability.

### **8.2 Future Directions**

The framework presented here provides a robust foundation, but several exciting avenues exist for future development and enhancement.

* **Full-Text Content Analysis:** The current scope of the agent ends with the successful retrieval of the PDF. A natural and powerful extension would be to add a subsequent module that uses multi-modal LLMs to "read" and analyze the content of the retrieved PDF. This could enable automated summarization, extraction of key findings, identification of methodologies and datasets used, and even advanced question-answering capabilities based on the paper's content.  
* **Handling of Supplementary Materials:** Modern research is often published with supplementary data, code repositories, and other materials. The agent could be extended to identify links to these materials on the article's landing page and attempt to retrieve them as well, creating a more complete package of the research output.  
* **Addressing Open Problems in Information Retrieval:** The agent's capabilities are ultimately constrained by the current state of AI and information retrieval technology. Future versions could incorporate research aimed at solving open problems, such as the lack of true iterative reasoning in Retrieval-Augmented Generation (RAG) systems.78 An advanced agent might be able to reason that its initial metadata is insufficient and initiate a new, more targeted search to find a missing piece of information, moving closer to a human-like research process.  
* **Federated Learning and Collaborative Agents:** A network of such agents could be deployed by different institutions. These agents could (with appropriate privacy safeguards) share anonymized data about the structure of publisher websites. If one agent learns how to navigate the download process on a particular journal's site, it could share that "navigation pattern" with others, allowing the entire system to adapt more quickly to changes on the web.

In conclusion, the agent designed in this report represents a significant step towards the automated, large-scale, and legally compliant aggregation of open access scientific knowledge. By thoughtfully combining established software engineering principles with the latest advances in artificial intelligence, it is possible to build a tool that can effectively navigate the complexities of the modern web and serve the foundational goal of open science: making knowledge accessible to all.

#### **Works cited**

1. Architecture of web scraping | Download Scientific Diagram \- ResearchGate, accessed August 3, 2025, [https://www.researchgate.net/figure/Architecture-of-web-scraping\_fig1\_347999311](https://www.researchgate.net/figure/Architecture-of-web-scraping_fig1_347999311)  
2. An intelligent design retrieval system for module-based products, accessed August 3, 2025, [https://mospace.umsystem.edu/xmlui/handle/10355/4085](https://mospace.umsystem.edu/xmlui/handle/10355/4085)  
3. Design and Development of a Multimodal Biomedical Information Retrieval System, accessed August 3, 2025, [https://lhncbc.nlm.nih.gov/LHC-publications/PDF/pub2012019.pdf](https://lhncbc.nlm.nih.gov/LHC-publications/PDF/pub2012019.pdf)  
4. Large-Scale Web Scraping: Techniques & Challenges \[2025\] \- Research AIMultiple, accessed August 3, 2025, [https://research.aimultiple.com/large-scale-web-scraping/](https://research.aimultiple.com/large-scale-web-scraping/)  
5. Implementing Web Scraping in Python with BeautifulSoup ..., accessed August 3, 2025, [https://www.geeksforgeeks.org/python/implementing-web-scraping-python-beautiful-soup/](https://www.geeksforgeeks.org/python/implementing-web-scraping-python-beautiful-soup/)  
6. Playwright vs Selenium : Which to choose in 2025 | BrowserStack, accessed August 3, 2025, [https://www.browserstack.com/guide/playwright-vs-selenium](https://www.browserstack.com/guide/playwright-vs-selenium)  
7. Fast and reliable end-to-end testing for modern web apps | Playwright Python, accessed August 3, 2025, [https://playwright.dev/python/](https://playwright.dev/python/)  
8. unpywall \- GitHub, accessed August 3, 2025, [https://github.com/unpywall](https://github.com/unpywall)  
9. habanero \- Read the Docs, accessed August 3, 2025, [https://habanero.readthedocs.io/](https://habanero.readthedocs.io/)  
10. unpywall/unpywall: Interfacing the Unpaywall Database ... \- GitHub, accessed August 3, 2025, [https://github.com/unpywall/unpywall](https://github.com/unpywall/unpywall)  
11. sckott/habanero: client for Crossref search API \- GitHub, accessed August 3, 2025, [https://github.com/sckott/habanero](https://github.com/sckott/habanero)  
12. (PDF) Key NLP Techniques for Identifying Student Interests: A Comprehensive Review, accessed August 3, 2025, [https://www.researchgate.net/publication/389992576\_Key\_NLP\_Techniques\_for\_Identifying\_Student\_Interests\_A\_Comprehensive\_Review](https://www.researchgate.net/publication/389992576_Key_NLP_Techniques_for_Identifying_Student_Interests_A_Comprehensive_Review)  
13. Extracting Information from Unstructured Text with NLP – (6 Ways) \- Accern, accessed August 3, 2025, [https://www.accern.com/resources/extracting-information-from-unstructured-text-with-nlp---6-ways](https://www.accern.com/resources/extracting-information-from-unstructured-text-with-nlp---6-ways)  
14. What Is NLP (Natural Language Processing)? \- IBM, accessed August 3, 2025, [https://www.ibm.com/think/topics/natural-language-processing](https://www.ibm.com/think/topics/natural-language-processing)  
15. LLM-Powered Metadata Extraction Algorithm \- MindCraft AI, accessed August 3, 2025, [https://mindcraft.ai/concepts/llm-powered-metadata-extraction-algorithm/](https://mindcraft.ai/concepts/llm-powered-metadata-extraction-algorithm/)  
16. Text-based classification of websites using self-hosted Large Language Models: An accuracy and efficiency analysis \- University of Twente Student Theses, accessed August 3, 2025, [https://essay.utwente.nl/101155/1/Sava\_BA\_EEMCS.pdf](https://essay.utwente.nl/101155/1/Sava_BA_EEMCS.pdf)  
17. Making LLMs Worth Every Penny: Resource-Limited Text Classification in Banking \- arXiv, accessed August 3, 2025, [https://arxiv.org/pdf/2311.06102](https://arxiv.org/pdf/2311.06102)  
18. A Study on Text Classification in the Age of Large Language Models \- MDPI, accessed August 3, 2025, [https://www.mdpi.com/2504-4990/6/4/129](https://www.mdpi.com/2504-4990/6/4/129)  
19. MOLE: Metadata Extraction and Validation in Scientific Papers Using LLMs \- arXiv, accessed August 3, 2025, [https://arxiv.org/html/2505.19800v1](https://arxiv.org/html/2505.19800v1)  
20. \[Literature Review\] MOLE: Metadata Extraction and Validation in Scientific Papers Using LLMs \- Moonlight, accessed August 3, 2025, [https://www.themoonlight.io/en/review/mole-metadata-extraction-and-validation-in-scientific-papers-using-llms](https://www.themoonlight.io/en/review/mole-metadata-extraction-and-validation-in-scientific-papers-using-llms)  
21. MOLE: Metadata Extraction and Validation in Scientific Papers Using LLMs \- ResearchGate, accessed August 3, 2025, [https://www.researchgate.net/publication/392134349\_MOLE\_Metadata\_Extraction\_and\_Validation\_in\_Scientific\_Papers\_Using\_LLMs](https://www.researchgate.net/publication/392134349_MOLE_Metadata_Extraction_and_Validation_in_Scientific_Papers_Using_LLMs)  
22. \[2505.19800\] MOLE: Metadata Extraction and Validation in Scientific Papers Using LLMs, accessed August 3, 2025, [https://arxiv.org/abs/2505.19800](https://arxiv.org/abs/2505.19800)  
23. MOLE: Metadata Extraction and Validation in Scientific Papers using LLMs \- Blog Post, accessed August 3, 2025, [https://ivul-kaust.github.io/MOLE/blog/](https://ivul-kaust.github.io/MOLE/blog/)  
24. Metadata Retrieval \- Crossref, accessed August 3, 2025, [https://www.crossref.org/documentation/retrieve-metadata/](https://www.crossref.org/documentation/retrieve-metadata/)  
25. Welcome to crossref's documentation\! — crossref 0.1.0 documentation, accessed August 3, 2025, [https://crossref.readthedocs.io/](https://crossref.readthedocs.io/)  
26. Crossref API, accessed August 3, 2025, [https://api.crossref.org/](https://api.crossref.org/)  
27. Documentation \- Cited-by \- Crossref, accessed August 3, 2025, [https://www.crossref.org/documentation/cited-by/](https://www.crossref.org/documentation/cited-by/)  
28. Unpaywall: An open database of 20 million free scholarly articles, accessed August 3, 2025, [https://unpaywall.org/](https://unpaywall.org/)  
29. REST API \- Unpaywall, accessed August 3, 2025, [https://unpaywall.org/products/api](https://unpaywall.org/products/api)  
30. Reference Coverage Analysis of OpenAlex compared to Web of Science and Scopus \- arXiv, accessed August 3, 2025, [https://arxiv.org/html/2401.16359v1](https://arxiv.org/html/2401.16359v1)  
31. Changes to Scopus Open Access (OA) document tagging, accessed August 3, 2025, [https://blog.scopus.com/changes-to-scopus-open-access-oa-document-tagging/](https://blog.scopus.com/changes-to-scopus-open-access-oa-document-tagging/)  
32. OpenAlex technical documentation: Overview, accessed August 3, 2025, [https://docs.openalex.org/](https://docs.openalex.org/)  
33. Entities overview \- OpenAlex technical documentation, accessed August 3, 2025, [https://docs.openalex.org/api-entities/entities-overview](https://docs.openalex.org/api-entities/entities-overview)  
34. API Overview | OpenAlex technical documentation, accessed August 3, 2025, [https://docs.openalex.org/how-to-use-the-api/api-overview](https://docs.openalex.org/how-to-use-the-api/api-overview)  
35. Unpaywall without Internet access? | by Horst Herb | Jun, 2025 \- Medium, accessed August 3, 2025, [https://medium.com/@horstherb/unpaywall-without-internet-access-2fea029f1179](https://medium.com/@horstherb/unpaywall-without-internet-access-2fea029f1179)  
36. About the data \- OpenAlex Support, accessed August 3, 2025, [https://help.openalex.org/hc/en-us/articles/24397285563671-About-the-data](https://help.openalex.org/hc/en-us/articles/24397285563671-About-the-data)  
37. Scholarly Communication Analytics: Analysing and reclassifying ..., accessed August 3, 2025, [https://subugoe.github.io/scholcomm\_analytics/posts/oalex\_oa\_status/](https://subugoe.github.io/scholcomm_analytics/posts/oalex_oa_status/)  
38. Data Format | Unpaywall, accessed August 3, 2025, [https://unpaywall.org/data-format](https://unpaywall.org/data-format)  
39. AutoWebGLM: A Large Language Model-based Web Navigating Agent \- arXiv, accessed August 3, 2025, [https://arxiv.org/html/2404.03648v2](https://arxiv.org/html/2404.03648v2)  
40. Meet WebAgent: DeepMind's New LLM that Follows Instructions and Complete Tasks on Websites | by Jesus Rodriguez | Towards AI, accessed August 3, 2025, [https://pub.towardsai.net/meet-webagent-deepminds-new-llm-that-follow-instructions-and-complete-tasks-on-websites-955d2b087a2d](https://pub.towardsai.net/meet-webagent-deepminds-new-llm-that-follow-instructions-and-complete-tasks-on-websites-955d2b087a2d)  
41. Hierarchical Prompting Assists Large Language Model on Web ..., accessed August 3, 2025, [https://aclanthology.org/2023.findings-emnlp.685/](https://aclanthology.org/2023.findings-emnlp.685/)  
42. WEBWALKER: BENCHMARKING LLMS IN WEB ... \- OpenReview, accessed August 3, 2025, [https://openreview.net/pdf/2b352174d4fd3d1aa111f8e857a4ce0e4d166c3c.pdf](https://openreview.net/pdf/2b352174d4fd3d1aa111f8e857a4ce0e4d166c3c.pdf)  
43. Automated Category and Trend Analysis of Scientific Articles on Ophthalmology Using Large Language Models: Development and Usability Study \- PubMed Central, accessed August 3, 2025, [https://pmc.ncbi.nlm.nih.gov/articles/PMC10998173/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10998173/)  
44. Bypassing Paywalls with Client-Side JavaScript Manipulation: A Technical Exploration | by Salt Creaitve | Medium, accessed August 3, 2025, [https://medium.com/@salt.creative/bypassing-paywalls-with-client-side-javascript-manipulation-a-technical-exploration-0f5759d04488](https://medium.com/@salt.creative/bypassing-paywalls-with-client-side-javascript-manipulation-a-technical-exploration-0f5759d04488)  
45. unpywall: Interfacing the Unpaywall Database with Python — unpywall MIT documentation, accessed August 3, 2025, [https://unpywall.readthedocs.io/](https://unpywall.readthedocs.io/)  
46. 7 Python Libraries For Web Scraping To Master Data Extraction \- ProjectPro, accessed August 3, 2025, [https://www.projectpro.io/article/python-libraries-for-web-scraping/625](https://www.projectpro.io/article/python-libraries-for-web-scraping/625)  
47. Beautiful Soup: Build a Web Scraper With Python, accessed August 3, 2025, [https://realpython.com/beautiful-soup-web-scraper-python/](https://realpython.com/beautiful-soup-web-scraper-python/)  
48. beautifulsoup4 \- PyPI, accessed August 3, 2025, [https://pypi.org/project/beautifulsoup4/](https://pypi.org/project/beautifulsoup4/)  
49. Tutorial: Web Scraping with Python BeautifulSoup and Requests Libraries | by Praise James, accessed August 3, 2025, [https://medium.com/@techwithpraisejames/web-scraping-with-beautifulsoup-and-requests-python-libraries-72c164b58316](https://medium.com/@techwithpraisejames/web-scraping-with-beautifulsoup-and-requests-python-libraries-72c164b58316)  
50. Selenium Grid (experimental) | Playwright Python, accessed August 3, 2025, [https://playwright.dev/python/docs/selenium-grid](https://playwright.dev/python/docs/selenium-grid)  
51. Installation | Playwright Python, accessed August 3, 2025, [https://playwright.dev/python/docs/intro](https://playwright.dev/python/docs/intro)  
52. Scholarly Communication Analytics: About us \- SUB Open, accessed August 3, 2025, [https://subugoe.github.io/scholcomm\_analytics/about.html](https://subugoe.github.io/scholcomm_analytics/about.html)  
53. unpywall \- Release MIT, accessed August 3, 2025, [https://unpywall.readthedocs.io/\_/downloads/en/latest/pdf/](https://unpywall.readthedocs.io/_/downloads/en/latest/pdf/)  
54. unpywall \- Interfacing the Unpaywall API with Python \- PyPI, accessed August 3, 2025, [https://pypi.org/project/unpywall/](https://pypi.org/project/unpywall/)  
55. unpywall: Interfacing the Unpaywall Database with Python ..., accessed August 3, 2025, [https://unpywall.readthedocs.io/en/latest/](https://unpywall.readthedocs.io/en/latest/)  
56. habanero \- PyPI, accessed August 3, 2025, [https://pypi.org/project/habanero/0.1.1/](https://pypi.org/project/habanero/0.1.1/)  
57. habanero \- PyPI, accessed August 3, 2025, [https://pypi.org/project/habanero/](https://pypi.org/project/habanero/)  
58. Blog \- Python and Ruby Libraries for accessing the Crossref API, accessed August 3, 2025, [https://www.crossref.org/blog/python-and-ruby-libraries-for-accessing-the-crossref-api/](https://www.crossref.org/blog/python-and-ruby-libraries-for-accessing-the-crossref-api/)  
59. CrossRef API — VOLT Virtual Online Library Tutorials, accessed August 3, 2025, [https://eps-libraries-berkeley.github.io/volt/Search/crossref\_library\_module.html](https://eps-libraries-berkeley.github.io/volt/Search/crossref_library_module.html)  
60. How to Get a Citation from DOI with Python\_habanero:一个用于访问学术数据库api的库, accessed August 3, 2025, [https://blog.csdn.net/sergeyyurkov1/article/details/130090743](https://blog.csdn.net/sergeyyurkov1/article/details/130090743)  
61. habanero \- Read the Docs, accessed August 3, 2025, [https://habanero.readthedocs.io/en/latest/](https://habanero.readthedocs.io/en/latest/)  
62. Anti Scraping Techniques To Prevent Scraping & How to Bypass Them | NetNut, accessed August 3, 2025, [https://netnut.io/anti-scraping/](https://netnut.io/anti-scraping/)  
63. Anti-Scraping Protection: A Comprehensive Guide \- Bytescare, accessed August 3, 2025, [https://bytescare.com/blog/anti-scraping-protection](https://bytescare.com/blog/anti-scraping-protection)  
64. Anti-scraping protections | Academy \- Apify Documentation, accessed August 3, 2025, [https://docs.apify.com/academy/anti-scraping](https://docs.apify.com/academy/anti-scraping)  
65. 7 Ways to Bypass CAPTCHA While Scraping: Quick Guide \- ZenRows, accessed August 3, 2025, [https://www.zenrows.com/blog/bypass-captcha-web-scraping](https://www.zenrows.com/blog/bypass-captcha-web-scraping)  
66. Undercover Operations: Scraping the Cybercrime Underground ..., accessed August 3, 2025, [https://www.sans.org/blog/undercover-operations-scraping-the-cybercrime-underground](https://www.sans.org/blog/undercover-operations-scraping-the-cybercrime-underground)  
67. Handling CAPTCHAs in Web Scraping: Tools and Techniques \- VOCSO Technologies, accessed August 3, 2025, [https://www.vocso.com/blog/handling-captchas-in-web-scraping-tools-and-techniques/](https://www.vocso.com/blog/handling-captchas-in-web-scraping-tools-and-techniques/)  
68. How To Bypass Anti-Bots With Python | ScrapeOps, accessed August 3, 2025, [https://scrapeops.io/python-web-scraping-playbook/python-how-to-bypass-anti-bots/](https://scrapeops.io/python-web-scraping-playbook/python-how-to-bypass-anti-bots/)  
69. How to bypass Captcha while Web Scraping \- Stack Overflow, accessed August 3, 2025, [https://stackoverflow.com/questions/75091821/how-to-bypass-captcha-while-web-scraping](https://stackoverflow.com/questions/75091821/how-to-bypass-captcha-while-web-scraping)  
70. How To Solve CAPTCHAs with Python \- ScrapeOps, accessed August 3, 2025, [https://scrapeops.io/python-web-scraping-playbook/python-how-to-solve-captchas/](https://scrapeops.io/python-web-scraping-playbook/python-how-to-solve-captchas/)  
71. Ethical Web Scraping: Principles and Practices \- DataCamp, accessed August 3, 2025, [https://www.datacamp.com/blog/ethical-web-scraping](https://www.datacamp.com/blog/ethical-web-scraping)  
72. Ethics & Legality of Webscraping \- Carpentry @ UCSB Library, accessed August 3, 2025, [https://carpentry.library.ucsb.edu/2022-05-12-ucsb-webscraping/06-Ethics-Legality-Webscraping/index.html](https://carpentry.library.ucsb.edu/2022-05-12-ucsb-webscraping/06-Ethics-Legality-Webscraping/index.html)  
73. Is Web Scraping Legal? Laws, Ethics, and Best Practices \- Research AIMultiple, accessed August 3, 2025, [https://research.aimultiple.com/is-web-scraping-legal/](https://research.aimultiple.com/is-web-scraping-legal/)  
74. Web Scraping for Research: Legal, Ethical, Institutional, and Scientific Considerations This is a non-peer reviewed working paper. \- arXiv, accessed August 3, 2025, [https://arxiv.org/html/2410.23432v1](https://arxiv.org/html/2410.23432v1)  
75. Data Research | School of Technology \- University of Cambridge, accessed August 3, 2025, [https://www.tech.cam.ac.uk/research-ethics/school-technology-research-ethics-guidance/data-research](https://www.tech.cam.ac.uk/research-ethics/school-technology-research-ethics-guidance/data-research)  
76. What are the standard evaluation metrics in IR? \- Milvus, accessed August 3, 2025, [https://milvus.io/ai-quick-reference/what-are-the-standard-evaluation-metrics-in-ir](https://milvus.io/ai-quick-reference/what-are-the-standard-evaluation-metrics-in-ir)  
77. Data extraction methods for systematic review (semi)automation ..., accessed August 3, 2025, [https://pmc.ncbi.nlm.nih.gov/articles/PMC8361807/](https://pmc.ncbi.nlm.nih.gov/articles/PMC8361807/)  
78. The Limitations and Advantages of Retrieval Augmented Generation (RAG), accessed August 3, 2025, [https://towardsdatascience.com/the-limitations-and-advantages-of-retrieval-augmented-generation-rag-9ec9b4ae3729/](https://towardsdatascience.com/the-limitations-and-advantages-of-retrieval-augmented-generation-rag-9ec9b4ae3729/)  
79. Limitations of Information Retrieval using Large Language Models \[LLMs\] | by Kushal Shah | PINC Innovations | Medium, accessed August 3, 2025, [https://medium.com/pinc-innovations/limitations-of-information-retrieval-using-large-language-models-llms-e9eba20d30be](https://medium.com/pinc-innovations/limitations-of-information-retrieval-using-large-language-models-llms-e9eba20d30be)