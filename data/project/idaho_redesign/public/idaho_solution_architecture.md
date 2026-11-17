## Platform Overview

A modern, accessible digital government platform built with low-code/no-code principles to modernize content management, search, and citizen engagement across Idaho.gov.

### Core Value Proposition

- **Accessibility First**: WCAG 2.1 AA compliance plus AAA Guideline 3.2.5 (Change on Request)
- **Cost Controlled**: Transparent visibility into AI/search costs with budget controls
- **Citizen Focused**: Fast, intelligent search with AI-powered chatbot assistance
- **Editor Friendly**: Non-technical content management with structured publishing

---
## Environment Architecture

The platform operates across multiple environments to ensure reliable development, testing, and production workflows. The architecture is split between Azure Infrastructure-as-Code (IaC) environments and WordPress application environments.

### Azure IaC Environments

**ITT Tenant (Development & Testing)**

- **ITT Dev**: Development environment for infrastructure testing and initial development work
- **ITT QA**: Quality assurance environment for testing infrastructure changes before production deployment
- **Service Connections**: Secure connections between environments Open Id Connect using federated identity credentials per resource group

**ITT Azure DevOps Hub**

- **Terraform Pipeline (CD)**: Continuous deployment pipeline for infrastructure provisioning
- **Build (CI)**: Continuous integration for infrastructure code validation
- **Service Connections**: Managed connections to various Azure resources (itt-oidc-dev, itt-oidc-qa, its-oidc-dev).

**ITS Tenant (Staging & Production)**

- **ITS Dev**: Pre-staging development environment for proving IaC integrity
- **ITS Staging**: Staging environment for ITS vetting
- **ITS Prod**: Live production environment serving Idaho.gov users
- **Federated Identity**: Secure credential management across all environments

### WordPress Environments

#### **ITT Dev/QA Environment**

- **Location**: ITT Azure Tenant
- **Components**:
    - Azure Virtual Machine hosting WordPress
    - Dev Azure DB for MySQL database instance
    - Dev WordPress instance with full development capabilities

****

- **Location**: ITT Azure Tenant
- **Components**:
    - Azure Virtual Machine for Dev/QA testing
    - Dev/QA Azure DB for MySQL database
    - Dev/QA WordPress instance for content and functionality testing

#### **ITS Dev/Prod Environment**

- **Location**: ITS On-Premises with Azure integration
- **Components**:
    - On-premises WordPress server (ITS managed)
    - Dev/Production MySQL database (SqlDump or plugin for data transfer)

### Environment Promotion Pipeline

**ITT Managed: Development → QA → ITS Dev** **ITS Managed: ITS Dev → ITS Staging → ITS Production**

1. **Development Phase**: Code and content development in ITT Dev environment
2. **Quality Assurance**: Automated and manual testing in ITT QA environment
3. **Cross-Tenant Deployment**: ITT deploys validated code to ITS Dev via OIDC service connection 
	1. Include change log documentation for quicker review
4. **ITS Staging**: ITS team promotes from ITS Dev to ITS Staging for final validation
5. **Production Deployment**: ITS team controls final deployment to production environment

**Deployment Controls:**

- ITT: Automated infrastructure provisioning via Terraform to ITT environments and ITS Dev
- ITS: Internal promotion pipeline for ITS Dev → Staging → Production
- Database migration and synchronization between environments
- Content promotion workflows with approval gates at tenant boundaries
- Rollback capabilities at each environment level

---
## System Architecture

### 1. Content Management Layer

**WordPress CMS Foundation**

- **Editing**: Advanced Custom Fields (ACF) + Elementor Pro for structured non technical manageable content
- **Theme**: ITS-approved theme or subtheme with Max Mega Menu plugin
- **Accessibility**: WCAG 2.1 AA/AAA enforced at development level
- **Performance**: WebP images, lazy loading, responsive design, SEO optimization via Elementor/WordPress best practices
- **Security**: WordPress built-in authentication, optional MFA via MiniOrange SAML SSO (client discretion)

### 2. Content Discovery & Indexing

**Automated Web Scraping Pipeline**

```
Subdomains Table → Logic Apps → Scraping Engine → Blob Storage → AI Search Index
```

**Scraping Strategy:**

- **Primary**: Azure Container Instances - Scrapy / scrappy-playwright for static HTML sites (fast, low cost)
- **Fallback**: For SPAs/JavaScript-heavy sites scrape network tab first. Second option is Playwright for rendering content then scrape
- **Content Extraction**: Metadata headers, cleaned text content, PDF documents
- **Navigation**: Follow sitemaps and robots.txt, respect configured depth limits, skip navigation elements
- **Enrichment**: Telemetry data integrated for content quality and performance tracking
- **Governance**: Subdomain table configurations control depth limits, page caps, file types, incremental updates (skip unchanged pages)

**Data Flow:**

1. Logic Apps orchestrates scheduled/manual scrapes
2. Optional pre-scrape preview (page counts, file sizes, estimated processing time)
3. Content scraped and enriched with metadata (subdomain, method, telemetry)
4. JSON documents stored in Blob Storage (staging → production)
5. Content chunked and indexed in Azure AI Search with embedding generation
6. AI skillsets perform entity extraction and metadata enrichment (automatic refresh for scheduled runs)

### 3. Intelligent Search System

**Hybrid Search Approach**

```
Query → Azure Function → AI Search (BM25 + Embeddings) → Ranked Results + Citations
```

**Features:**

- **Hybrid Retrieval**: Combines keyword search (BM25) with semantic embeddings (Azure OpenAI)
- **AI Skillsets**: Entity extraction and automated metadata enrichment during indexing
- **Cost Control**: Embedding deduplication via content hashing, usage monitoring
- **Quality**: Optional Semantic Ranker for precision improvements
- **Transparency**: Full citation tracking for all results

### 4. AI Chatbot Integration

**Copilot Studio Agent**

**Implementation Options:**

- **Option A**: Direct Line Web Chat (simpler, WordPress REST endpoint for token exchange)
- **Option B**: Microsoft 365 Agents SDK via Node/.NET gateway service

**Features:**

- Domain-specific knowledge from indexed content
- Source citations for all responses
- Rate limiting and security controls
- WCAG compliant interface

---

## Technical Stack

| **Component**     | **Technology**                                  | **Purpose**                            |
| ----------------- | ----------------------------------------------- | -------------------------------------- |
| **CMS**           | WordPress + ACF + Elementor Pro (MySQL/MariaDB) | Content management & publishing        |
| **Orchestration** | Azure Logic Apps                                | Workflow automation & scraping control |
| **Scraping**      | Scrapy + Scrapy-Playwright                      | Content discovery & extraction         |
| **Storage**       | Azure Blob Storage                              | Scraped content & metadata             |
| **Search**        | Azure AI Search + OpenAI Embeddings             | Intelligent search & retrieval         |
| **AI Chat**       | Copilot Studio                                  | Conversational AI interface            |
| **Monitoring**    | Application Insights + Log Analytics            | Performance & cost tracking            |

---

## Key Operational Features

### Accessibility Compliance (WCAG 2.1)

- **Level AA**: All standard requirements met
- **Level AAA**: Specific implementation of Guideline 3.2.5 (Change on Request - user control over content changes)
- **Testing**: Automated + manual screen reader and keyboard navigation testing

### Cost Management

- Post-scrape cost analysis via Application Insights and Log Analytics
- Subdomain-level configuration controls (depth limits, page caps)
- Pre-scrape preview option for size estimation _(exploration: token/cost estimation methods)_
- Admin dashboards for usage visibility
- Content hash-based deduplication to avoid duplicate embeddings

### Quality Assurance

- Staging environment for content review before indexing
- Manual scrape controls and test runs
- Feedback loops for search ranking improvements
- Comprehensive telemetry and error tracking

---

## Performance Targets

- **Page Load**: < 3 seconds initial load
- **Search Response**: < 2 seconds for query results
- **Accessibility**: Zero blocking violations
- **Uptime**: 99.9% availability target

---

## Security & Compliance

- **Authentication**: WordPress built-in user management, optional MFA via MiniOrange SAML SSO plugin (client discretion)
- **Data Protection**: HTTPS everywhere, CORS configuration, PHP backend proxy to API Management
- **Access Control**: Role-based permissions, ITS-approved components
- **Compliance**: ADA Title II, Section 508, WCAG 2.1 standards




