 # SNS UCIER Discovery Packet

Generated from local repository and PostgreSQL schema.
Root: C:\dev\sns emr\backend
Database: sns_emr_dev_clean


## 1. Repository Summary

Current directory:

Path                  
----                  
C:\dev\sns emr\backend



Python file count under app:
445

Top-level app folders:

FullName                               
--------                               
C:\dev\sns emr\backend\app\api         
C:\dev\sns emr\backend\app\billing     
C:\dev\sns emr\backend\app\compliance  
C:\dev\sns emr\backend\app\config      
C:\dev\sns emr\backend\app\constants   
C:\dev\sns emr\backend\app\core        
C:\dev\sns emr\backend\app\db          
C:\dev\sns emr\backend\app\dependencies
C:\dev\sns emr\backend\app\domain      
C:\dev\sns emr\backend\app\examples    
C:\dev\sns emr\backend\app\guards      
C:\dev\sns emr\backend\app\jobs        
C:\dev\sns emr\backend\app\models      
C:\dev\sns emr\backend\app\rules       
C:\dev\sns emr\backend\app\schemas     
C:\dev\sns emr\backend\app\scripts     
C:\dev\sns emr\backend\app\security    
C:\dev\sns emr\backend\app\services    
C:\dev\sns emr\backend\app\tenancy     
C:\dev\sns emr\backend\app\tenants     
C:\dev\sns emr\backend\app\utils       
C:\dev\sns emr\backend\app\__pycache__ 




## 2. Python Files Under app


FullName                                                                          
--------                                                                          
C:\dev\sns emr\backend\app\__init__.py                                            
C:\dev\sns emr\backend\app\api\__init__.py                                        
C:\dev\sns emr\backend\app\api\admin\__init__.py                                  
C:\dev\sns emr\backend\app\api\admin\chart_export.py                              
C:\dev\sns emr\backend\app\api\admin_jobs.py                                      
C:\dev\sns emr\backend\app\api\admin_reminders.py                                 
C:\dev\sns emr\backend\app\api\admission.py                                       
C:\dev\sns emr\backend\app\api\admission_authorization.py                         
C:\dev\sns emr\backend\app\api\admission_diagnosis.py                             
C:\dev\sns emr\backend\app\api\admissions.py                                      
C:\dev\sns emr\backend\app\api\adr_exports.py                                     
C:\dev\sns emr\backend\app\api\adr_readiness.py                                   
C:\dev\sns emr\backend\app\api\audit_dashboard.py                                 
C:\dev\sns emr\backend\app\api\auth.py                                            
C:\dev\sns emr\backend\app\api\auth_reauth.py                                     
C:\dev\sns emr\backend\app\api\auth_whoami.py                                     
C:\dev\sns emr\backend\app\api\benefits.py                                        
C:\dev\sns emr\backend\app\api\billing_835.py                                     
C:\dev\sns emr\backend\app\api\certifications.py                                  
C:\dev\sns emr\backend\app\api\chha_pocs.py                                       
C:\dev\sns emr\backend\app\api\clinical_notes.py                                  
C:\dev\sns emr\backend\app\api\clinical_notes\__init__.py                         
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                           
C:\dev\sns emr\backend\app\api\clinical_translation.py                            
C:\dev\sns emr\backend\app\api\communications_log\router.py                       
C:\dev\sns emr\backend\app\api\communications_log\schemas.py                      
C:\dev\sns emr\backend\app\api\compliance.py                                      
C:\dev\sns emr\backend\app\api\coverage.py                                        
C:\dev\sns emr\backend\app\api\dashboard\router.py                                
C:\dev\sns emr\backend\app\api\debug.py                                           
C:\dev\sns emr\backend\app\api\dev_test.py                                        
C:\dev\sns emr\backend\app\api\discharges.py                                      
C:\dev\sns emr\backend\app\api\documents.py                                       
C:\dev\sns emr\backend\app\api\eligibility.py                                     
C:\dev\sns emr\backend\app\api\eligibility\__init__.py                            
C:\dev\sns emr\backend\app\api\eligibility\routes.py                              
C:\dev\sns emr\backend\app\api\external_substances.py                             
C:\dev\sns emr\backend\app\api\f2f.py                                             
C:\dev\sns emr\backend\app\api\idg\router.py                                      
C:\dev\sns emr\backend\app\api\internal_superuser.py                              
C:\dev\sns emr\backend\app\api\internal_tasks.py                                  
C:\dev\sns emr\backend\app\api\internal_training.py                               
C:\dev\sns emr\backend\app\api\med_reconciliation.py                              
C:\dev\sns emr\backend\app\api\medications.py                                     
C:\dev\sns emr\backend\app\api\noe.py                                             
C:\dev\sns emr\backend\app\api\notes.py                                           
C:\dev\sns emr\backend\app\api\notifications.py                                   
C:\dev\sns emr\backend\app\api\patient_assignments.py                             
C:\dev\sns emr\backend\app\api\patients.py                                        
C:\dev\sns emr\backend\app\api\print.py                                           
C:\dev\sns emr\backend\app\api\registry.py                                        
C:\dev\sns emr\backend\app\api\regulatory\__init__.py                             
C:\dev\sns emr\backend\app\api\regulatory\reports.py                              
C:\dev\sns emr\backend\app\api\router.py                                          
C:\dev\sns emr\backend\app\api\routes\__init__.py                                 
C:\dev\sns emr\backend\app\api\routes\forms.py                                    
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                             
C:\dev\sns emr\backend\app\api\rules\__init__.py                                  
C:\dev\sns emr\backend\app\api\rules\routes.py                                    
C:\dev\sns emr\backend\app\api\safety_assessments.py                              
C:\dev\sns emr\backend\app\api\schemas\__init__.py                                
C:\dev\sns emr\backend\app\api\schemas\task.py                                    
C:\dev\sns emr\backend\app\api\schemas\task_read.py                               
C:\dev\sns emr\backend\app\api\schemas\task_write.py                              
C:\dev\sns emr\backend\app\api\soc_orders.py                                      
C:\dev\sns emr\backend\app\api\support_reference.py                               
C:\dev\sns emr\backend\app\api\survey.py                                          
C:\dev\sns emr\backend\app\api\task_completion.py                                 
C:\dev\sns emr\backend\app\api\task_scheduling.py                                 
C:\dev\sns emr\backend\app\api\tasks.py                                           
C:\dev\sns emr\backend\app\api\visits.py                                          
C:\dev\sns emr\backend\app\billing\__init__.py                                    
C:\dev\sns emr\backend\app\billing\api\__init__.py                                
C:\dev\sns emr\backend\app\billing\api\audit_router.py                            
C:\dev\sns emr\backend\app\billing\api\billing_queue_router.py                    
C:\dev\sns emr\backend\app\billing\api\billing_router.py                          
C:\dev\sns emr\backend\app\billing\api\claim_status_router.py                     
C:\dev\sns emr\backend\app\billing\api\export_router.py                           
C:\dev\sns emr\backend\app\billing\api\tenant_router.py                           
C:\dev\sns emr\backend\app\billing\audit_store.py                                 
C:\dev\sns emr\backend\app\billing\engine\billing_engine.py                       
C:\dev\sns emr\backend\app\billing\issues\issue_model.py                          
C:\dev\sns emr\backend\app\billing\issues\issue_service.py                        
C:\dev\sns emr\backend\app\billing\models\__init__.py                             
C:\dev\sns emr\backend\app\billing\models\authorization.py                        
C:\dev\sns emr\backend\app\billing\models\billing_cycle.py                        
C:\dev\sns emr\backend\app\billing\models\billing_snapshot.py                     
C:\dev\sns emr\backend\app\billing\models\billing_summary.py                      
C:\dev\sns emr\backend\app\billing\models\claim_export_log.py                     
C:\dev\sns emr\backend\app\billing\models\contract.py                             
C:\dev\sns emr\backend\app\billing\models\loc_events.py                           
C:\dev\sns emr\backend\app\billing\models\orders_snapshot.py                      
C:\dev\sns emr\backend\app\billing\models\patient_pos.py                          
C:\dev\sns emr\backend\app\billing\models\payer.py                                
C:\dev\sns emr\backend\app\billing\models\visit_minutes.py                        
C:\dev\sns emr\backend\app\billing\overrides\override_model.py                    
C:\dev\sns emr\backend\app\billing\overrides\override_service.py                  
C:\dev\sns emr\backend\app\billing\schemas\billing_schema.py                      
C:\dev\sns emr\backend\app\billing\security.py                                    
C:\dev\sns emr\backend\app\billing\services\billing_queue_service.py              
C:\dev\sns emr\backend\app\billing\services\billing_schema.py                     
C:\dev\sns emr\backend\app\billing\services\claim_export_service.py               
C:\dev\sns emr\backend\app\billing\services\claim_segment_service.py              
C:\dev\sns emr\backend\app\billing\services\edi_builder.py                        
C:\dev\sns emr\backend\app\billing\services\loc_segment_service.py                
C:\dev\sns emr\backend\app\billing\services\payer_service.py                      
C:\dev\sns emr\backend\app\billing\services\pos_to_loc_service.py                 
C:\dev\sns emr\backend\app\billing\services\revenue_service.py                    
C:\dev\sns emr\backend\app\billing\services\unit_service.py                       
C:\dev\sns emr\backend\app\billing\snapshots\snapshot_service.py                  
C:\dev\sns emr\backend\app\billing\store.py                                       
C:\dev\sns emr\backend\app\billing\validators\claim_validator.py                  
C:\dev\sns emr\backend\app\billing\validators\idg_validator.py                    
C:\dev\sns emr\backend\app\billing\validators\loc_validator.py                    
C:\dev\sns emr\backend\app\billing\validators\order_validator.py                  
C:\dev\sns emr\backend\app\billing\validators\poc_validator.py                    
C:\dev\sns emr\backend\app\compliance\achc\__init__.py                            
C:\dev\sns emr\backend\app\compliance\achc\documentation_timeliness.py            
C:\dev\sns emr\backend\app\compliance\cdph\__init__.py                            
C:\dev\sns emr\backend\app\compliance\cdph\california_specific.py                 
C:\dev\sns emr\backend\app\compliance\chap\__init__.py                            
C:\dev\sns emr\backend\app\compliance\chap\chap_core.py                           
C:\dev\sns emr\backend\app\compliance\cms\__init__.py                             
C:\dev\sns emr\backend\app\compliance\cms\evidence.py                             
C:\dev\sns emr\backend\app\compliance\cms\poc_update.py                           
C:\dev\sns emr\backend\app\compliance\registry.py                                 
C:\dev\sns emr\backend\app\compliance\rule_loader.py                              
C:\dev\sns emr\backend\app\compliance\runbooks\__init__.py                        
C:\dev\sns emr\backend\app\compliance\runbooks\generator.py                       
C:\dev\sns emr\backend\app\compliance\runbooks\templates.py                       
C:\dev\sns emr\backend\app\compliance\tjc\__init__.py                             
C:\dev\sns emr\backend\app\compliance\tjc\survey_tracers.py                       
C:\dev\sns emr\backend\app\compliance\types.py                                    
C:\dev\sns emr\backend\app\config\lcd\loader.py                                   
C:\dev\sns emr\backend\app\constants\guardrail_messages.py                        
C:\dev\sns emr\backend\app\core\__init__.py                                       
C:\dev\sns emr\backend\app\core\audit_events.py                                   
C:\dev\sns emr\backend\app\core\audit_middleware.py                               
C:\dev\sns emr\backend\app\core\auth.py                                           
C:\dev\sns emr\backend\app\core\authorization.py                                  
C:\dev\sns emr\backend\app\core\bulk_reauth_guard.py                              
C:\dev\sns emr\backend\app\core\bulk_rules.py                                     
C:\dev\sns emr\backend\app\core\dashboard_auth.py                                 
C:\dev\sns emr\backend\app\core\database.py                                       
C:\dev\sns emr\backend\app\core\db.py                                             
C:\dev\sns emr\backend\app\core\db_session.py                                     
C:\dev\sns emr\backend\app\core\db_tenant_dependency.py                           
C:\dev\sns emr\backend\app\core\enum_normalizer.py                                
C:\dev\sns emr\backend\app\core\env.py                                            
C:\dev\sns emr\backend\app\core\flag_rules_loader.py                              
C:\dev\sns emr\backend\app\core\idle_timeout_middleware.py                        
C:\dev\sns emr\backend\app\core\middleware\clinical_access_guard.py               
C:\dev\sns emr\backend\app\core\middleware\support_mfa_guard.py                   
C:\dev\sns emr\backend\app\core\permissions.py                                    
C:\dev\sns emr\backend\app\core\role_guards.py                                    
C:\dev\sns emr\backend\app\core\rule_enforcement.py                               
C:\dev\sns emr\backend\app\core\security.py                                       
C:\dev\sns emr\backend\app\core\security_deps.py                                  
C:\dev\sns emr\backend\app\core\settings.py                                       
C:\dev\sns emr\backend\app\core\sync_db.py                                        
C:\dev\sns emr\backend\app\core\task_completion_guard.py                          
C:\dev\sns emr\backend\app\core\tenant_context.py                                 
C:\dev\sns emr\backend\app\core\tenant_orm_filters.py                             
C:\dev\sns emr\backend\app\core\tenant_resolver.py                                
C:\dev\sns emr\backend\app\core\tenant_routing_middleware.py                      
C:\dev\sns emr\backend\app\core\tenant_schema_context.py                          
C:\dev\sns emr\backend\app\core\user_session_reference.py                         
C:\dev\sns emr\backend\app\core\user_session_reference_store.py                   
C:\dev\sns emr\backend\app\core\visit_type_normalizer.py                          
C:\dev\sns emr\backend\app\core\visit_types.py                                    
C:\dev\sns emr\backend\app\db\__init__.py                                         
C:\dev\sns emr\backend\app\db\base.py                                             
C:\dev\sns emr\backend\app\db\db_tenant.py                                        
C:\dev\sns emr\backend\app\db\reflection.py                                       
C:\dev\sns emr\backend\app\db\session.py                                          
C:\dev\sns emr\backend\app\db_request_dependency.py                               
C:\dev\sns emr\backend\app\db_tenant_dependency.py                                
C:\dev\sns emr\backend\app\dependencies\auth.py                                   
C:\dev\sns emr\backend\app\domain\care_model_engine.py                            
C:\dev\sns emr\backend\app\domain\forms\__init__.py                               
C:\dev\sns emr\backend\app\domain\forms\discipline_rules.py                       
C:\dev\sns emr\backend\app\domain\forms\enums.py                                  
C:\dev\sns emr\backend\app\domain\forms\form_registry.py                          
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                
C:\dev\sns emr\backend\app\domain\forms\module_registry.py                        
C:\dev\sns emr\backend\app\domain\forms\package_schemas.py                        
C:\dev\sns emr\backend\app\domain\poc\poc_task_rules.py                           
C:\dev\sns emr\backend\app\domain\tasks\__init__.py                               
C:\dev\sns emr\backend\app\domain\tasks\clinical_review_task_engine.py            
C:\dev\sns emr\backend\app\domain\tasks\task_escalation_routing.py                
C:\dev\sns emr\backend\app\domain\tasks\task_form_rules.py                        
C:\dev\sns emr\backend\app\domain\visits.py                                       
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py       
C:\dev\sns emr\backend\app\main.py                                                
C:\dev\sns emr\backend\app\models\__init__.py                                     
C:\dev\sns emr\backend\app\models\admission.py                                    
C:\dev\sns emr\backend\app\models\admission_status_history.py                     
C:\dev\sns emr\backend\app\models\amendment.py                                    
C:\dev\sns emr\backend\app\models\assessment.py                                   
C:\dev\sns emr\backend\app\models\assessment_discrepancy.py                       
C:\dev\sns emr\backend\app\models\assessment_reference.py                         
C:\dev\sns emr\backend\app\models\audit_log.py                                    
C:\dev\sns emr\backend\app\models\base.py                                         
C:\dev\sns emr\backend\app\models\benefit_period.py                               
C:\dev\sns emr\backend\app\models\certification.py                                
C:\dev\sns emr\backend\app\models\chha_poc.py                                     
C:\dev\sns emr\backend\app\models\chha_visit_outcome.py                           
C:\dev\sns emr\backend\app\models\chha_visit_task_result.py                       
C:\dev\sns emr\backend\app\models\clinical_note.py                                
C:\dev\sns emr\backend\app\models\clinical_workflow_map.py                        
C:\dev\sns emr\backend\app\models\communications_log.py                           
C:\dev\sns emr\backend\app\models\document_idg_resolution.py                      
C:\dev\sns emr\backend\app\models\document_notification.py                        
C:\dev\sns emr\backend\app\models\document_record.py                              
C:\dev\sns emr\backend\app\models\drug_alias.py                                   
C:\dev\sns emr\backend\app\models\dx_primary_policy.py                            
C:\dev\sns emr\backend\app\models\eligibility.py                                  
C:\dev\sns emr\backend\app\models\eligibility_decision.py                         
C:\dev\sns emr\backend\app\models\enums.py                                        
C:\dev\sns emr\backend\app\models\external_substance.py                           
C:\dev\sns emr\backend\app\models\f2f_encounter.py                                
C:\dev\sns emr\backend\app\models\form.py                                         
C:\dev\sns emr\backend\app\models\form_module.py                                  
C:\dev\sns emr\backend\app\models\form_package_module.py                          
C:\dev\sns emr\backend\app\models\form_registry_model.py                          
C:\dev\sns emr\backend\app\models\icd10_hospice_policy.py                         
C:\dev\sns emr\backend\app\models\icd10_master.py                                 
C:\dev\sns emr\backend\app\models\idg_attendee.py                                 
C:\dev\sns emr\backend\app\models\idg_justification.py                            
C:\dev\sns emr\backend\app\models\idg_md_attestation.py                           
C:\dev\sns emr\backend\app\models\idg_meeting.py                                  
C:\dev\sns emr\backend\app\models\idg_note.py                                     
C:\dev\sns emr\backend\app\models\idg_review.py                                   
C:\dev\sns emr\backend\app\models\idg_signature.py                                
C:\dev\sns emr\backend\app\models\idg_signature_tracker.py                        
C:\dev\sns emr\backend\app\models\incident_report.py                              
C:\dev\sns emr\backend\app\models\interface.py                                    
C:\dev\sns emr\backend\app\models\med_normalization.py                            
C:\dev\sns emr\backend\app\models\med_reconciliation.py                           
C:\dev\sns emr\backend\app\models\med_reconciliation_audit_log.py                 
C:\dev\sns emr\backend\app\models\medication.py                                   
C:\dev\sns emr\backend\app\models\notification.py                                 
C:\dev\sns emr\backend\app\models\patient.py                                      
C:\dev\sns emr\backend\app\models\patient_assignment.py                           
C:\dev\sns emr\backend\app\models\patient_diagnosis.py                            
C:\dev\sns emr\backend\app\models\patient_facesheet.py                            
C:\dev\sns emr\backend\app\models\patient_insurance.py                            
C:\dev\sns emr\backend\app\models\patient_payer.py                                
C:\dev\sns emr\backend\app\models\payer.py                                        
C:\dev\sns emr\backend\app\models\plan_of_care.py                                 
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                         
C:\dev\sns emr\backend\app\models\poc.py                                          
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                       
C:\dev\sns emr\backend\app\models\refusal.py                                      
C:\dev\sns emr\backend\app\models\rn_recert_assessment.py                         
C:\dev\sns emr\backend\app\models\role.py                                         
C:\dev\sns emr\backend\app\models\safety_assessment.py                            
C:\dev\sns emr\backend\app\models\service_coverage_decision.py                    
C:\dev\sns emr\backend\app\models\sfv_requirement.py                              
C:\dev\sns emr\backend\app\models\survey_access.py                                
C:\dev\sns emr\backend\app\models\task.py                                         
C:\dev\sns emr\backend\app\models\tenant.py                                       
C:\dev\sns emr\backend\app\models\tenant_mixin.py                                 
C:\dev\sns emr\backend\app\models\tenant_rule_toggle.py                           
C:\dev\sns emr\backend\app\models\user.py                                         
C:\dev\sns emr\backend\app\models\visit.py                                        
C:\dev\sns emr\backend\app\rules\base.py                                          
C:\dev\sns emr\backend\app\rules\diagnosis\prohibited_primary_dx_prefix.py        
C:\dev\sns emr\backend\app\rules\eligibility\chf_readiness.py                     
C:\dev\sns emr\backend\app\rules\eligibility\copd_readiness.py                    
C:\dev\sns emr\backend\app\rules\eligibility\end_stage_parkinsons.py              
C:\dev\sns emr\backend\app\rules\eligibility\esrd_readiness.py                    
C:\dev\sns emr\backend\app\rules\eligibility\functional_decline_readiness.py      
C:\dev\sns emr\backend\app\rules\enforcement.py                                   
C:\dev\sns emr\backend\app\rules\registry.py                                      
C:\dev\sns emr\backend\app\schemas\__init__.py                                    
C:\dev\sns emr\backend\app\schemas\admission_requests.py                          
C:\dev\sns emr\backend\app\schemas\adr_audit.py                                   
C:\dev\sns emr\backend\app\schemas\f2f.py                                         
C:\dev\sns emr\backend\app\schemas\poc_generation.py                              
C:\dev\sns emr\backend\app\schemas\safety_assessment.py                           
C:\dev\sns emr\backend\app\schemas\translation.py                                 
C:\dev\sns emr\backend\app\scripts\backfill_audit_hash_chain.py                   
C:\dev\sns emr\backend\app\scripts\backfill_med_recon_duplicate_backlog.py        
C:\dev\sns emr\backend\app\security\__init__.py                                   
C:\dev\sns emr\backend\app\security\deps.py                                       
C:\dev\sns emr\backend\app\services\__init__.py                                   
C:\dev\sns emr\backend\app\services\admission\__init__.py                         
C:\dev\sns emr\backend\app\services\admission\admission_guardrail_service.py      
C:\dev\sns emr\backend\app\services\admission\admission_readiness_gate.py         
C:\dev\sns emr\backend\app\services\admission\admission_service.py                
C:\dev\sns emr\backend\app\services\admission\admission_status_engine.py          
C:\dev\sns emr\backend\app\services\admission\admission_status_history_service.py 
C:\dev\sns emr\backend\app\services\admission\admission_task_generation_service.py
C:\dev\sns emr\backend\app\services\admission\admission_workflow_service.py       
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py          
C:\dev\sns emr\backend\app\services\admission\transfer_validation_service.py      
C:\dev\sns emr\backend\app\services\admission_authorization_service.py            
C:\dev\sns emr\backend\app\services\admission_cloning_service.py                  
C:\dev\sns emr\backend\app\services\admission_dx_validation_engine.py             
C:\dev\sns emr\backend\app\services\admission_guardrails_service.py               
C:\dev\sns emr\backend\app\services\admission_status_history_writer.py            
C:\dev\sns emr\backend\app\services\admission_workflow_service.py                 
C:\dev\sns emr\backend\app\services\adr_audit_service.py                          
C:\dev\sns emr\backend\app\services\adr_pdf_utils.py                              
C:\dev\sns emr\backend\app\services\adr_schema_map.py                             
C:\dev\sns emr\backend\app\services\audit_events.py                               
C:\dev\sns emr\backend\app\services\audit_logger.py                               
C:\dev\sns emr\backend\app\services\awareness_group.py                            
C:\dev\sns emr\backend\app\services\benefit_period_resolver.py                    
C:\dev\sns emr\backend\app\services\benefit_period_service.py                     
C:\dev\sns emr\backend\app\services\benefit_periods.py                            
C:\dev\sns emr\backend\app\services\bereavement_aggregation_engine.py             
C:\dev\sns emr\backend\app\services\care_model_service.py                         
C:\dev\sns emr\backend\app\services\certification_service.py                      
C:\dev\sns emr\backend\app\services\chart_pdf.py                                  
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                       
C:\dev\sns emr\backend\app\services\clinical_discipline_mapping.py                
C:\dev\sns emr\backend\app\services\clinical_note_service.py                      
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                  
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                     
C:\dev\sns emr\backend\app\services\communications_log_alerts.py                  
C:\dev\sns emr\backend\app\services\communications_log_service.py                 
C:\dev\sns emr\backend\app\services\coverage_audit_logger.py                      
C:\dev\sns emr\backend\app\services\coverage_resolver.py                          
C:\dev\sns emr\backend\app\services\dashboard_service.py                          
C:\dev\sns emr\backend\app\services\diagnosis_sync_service.py                     
C:\dev\sns emr\backend\app\services\document_flagger.py                           
C:\dev\sns emr\backend\app\services\document_notifications.py                     
C:\dev\sns emr\backend\app\services\document_reminders.py                         
C:\dev\sns emr\backend\app\services\dx_policy.py                                  
C:\dev\sns emr\backend\app\services\dynamic_condition_detection_engine.py         
C:\dev\sns emr\backend\app\services\edi_835_parser.py                             
C:\dev\sns emr\backend\app\services\eligibility\adl_dependency_service.py         
C:\dev\sns emr\backend\app\services\eligibility\config_hash.py                    
C:\dev\sns emr\backend\app\services\eligibility\eligibility_registry_service.py   
C:\dev\sns emr\backend\app\services\eligibility\eligibility_snapshot_service.py   
C:\dev\sns emr\backend\app\services\eligibility\eligibility_summary_service.py    
C:\dev\sns emr\backend\app\services\eligibility\engine.py                         
C:\dev\sns emr\backend\app\services\eligibility\evidence_harvester.py             
C:\dev\sns emr\backend\app\services\eligibility\lcd_loader.py                     
C:\dev\sns emr\backend\app\services\escalation.py                                 
C:\dev\sns emr\backend\app\services\f2f_service.py                                
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                        
C:\dev\sns emr\backend\app\services\icd10_policy_service.py                       
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                     
C:\dev\sns emr\backend\app\services\idg_completeness.py                           
C:\dev\sns emr\backend\app\services\idg_compliance.py                             
C:\dev\sns emr\backend\app\services\idg_dashboard.py                              
C:\dev\sns emr\backend\app\services\idg_dashboard_api.py                          
C:\dev\sns emr\backend\app\services\idg_enforcement.py                            
C:\dev\sns emr\backend\app\services\idg_engine.py                                 
C:\dev\sns emr\backend\app\services\idg_finalize.py                               
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                       
C:\dev\sns emr\backend\app\services\idg_meeting_bulk.py                           
C:\dev\sns emr\backend\app\services\idg_meeting_scheduler.py                      
C:\dev\sns emr\backend\app\services\idg_pdf.py                                    
C:\dev\sns emr\backend\app\services\idg_remediation.py                            
C:\dev\sns emr\backend\app\services\idg_reminder.py                               
C:\dev\sns emr\backend\app\services\idg_review_automation.py                      
C:\dev\sns emr\backend\app\services\idg_review_service.py                         
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                           
C:\dev\sns emr\backend\app\services\idg_signature_actions.py                      
C:\dev\sns emr\backend\app\services\idg_signature_tasks.py                        
C:\dev\sns emr\backend\app\services\idg_signature_validation.py                   
C:\dev\sns emr\backend\app\services\idg_task_engine.py                            
C:\dev\sns emr\backend\app\services\idg_task_generator.py                         
C:\dev\sns emr\backend\app\services\idg_validator.py                              
C:\dev\sns emr\backend\app\services\level_of_care_overlap_guard.py                
C:\dev\sns emr\backend\app\services\med_reconciliation_audit_service.py           
C:\dev\sns emr\backend\app\services\med_reconciliation_comparison.py              
C:\dev\sns emr\backend\app\services\med_reconciliation_comparison_engine.py       
C:\dev\sns emr\backend\app\services\med_reconciliation_dedup_service.py           
C:\dev\sns emr\backend\app\services\med_reconciliation_import_service.py          
C:\dev\sns emr\backend\app\services\med_reconciliation_normalizer.py              
C:\dev\sns emr\backend\app\services\med_safety.py                                 
C:\dev\sns emr\backend\app\services\medication_alias_service.py                   
C:\dev\sns emr\backend\app\services\mrn.py                                        
C:\dev\sns emr\backend\app\services\notification_engine.py                        
C:\dev\sns emr\backend\app\services\overdue_service.py                            
C:\dev\sns emr\backend\app\services\patient_assignment_service.py                 
C:\dev\sns emr\backend\app\services\patient_lifecycle.py                          
C:\dev\sns emr\backend\app\services\patients.py                                   
C:\dev\sns emr\backend\app\services\payer_validation.py                           
C:\dev\sns emr\backend\app\services\payment_service.py                            
C:\dev\sns emr\backend\app\services\pdf_signature.py                              
C:\dev\sns emr\backend\app\services\poc_compiler_rn_mapper.py                     
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                       
C:\dev\sns emr\backend\app\services\poc_engine.py                                 
C:\dev\sns emr\backend\app\services\poc_generation_service.py                     
C:\dev\sns emr\backend\app\services\poc_review_gate.py                            
C:\dev\sns emr\backend\app\services\poc_rule_loader.py                            
C:\dev\sns emr\backend\app\services\poc_service.py                                
C:\dev\sns emr\backend\app\services\poc_task_engine.py                            
C:\dev\sns emr\backend\app\services\poc_task_service.py                           
C:\dev\sns emr\backend\app\services\poc_update_automation.py                      
C:\dev\sns emr\backend\app\services\poc_update_tasks.py                           
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                    
C:\dev\sns emr\backend\app\services\poc_warning_tasks.py                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py 
C:\dev\sns emr\backend\app\services\recert_f2f_enforcement.py                     
C:\dev\sns emr\backend\app\services\recert_f2f_tasks.py                           
C:\dev\sns emr\backend\app\services\recipient_resolution.py                       
C:\dev\sns emr\backend\app\services\reconciliation_review_task_service.py         
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                
C:\dev\sns emr\backend\app\services\refusal_engine.py                             
C:\dev\sns emr\backend\app\services\regulatory_report_service.py                  
C:\dev\sns emr\backend\app\services\rules_dry_run.py                              
C:\dev\sns emr\backend\app\services\safety_assessments.py                         
C:\dev\sns emr\backend\app\services\security_activity_logger.py                   
C:\dev\sns emr\backend\app\services\sfv_completion.py                             
C:\dev\sns emr\backend\app\services\sfv_engine.py                                 
C:\dev\sns emr\backend\app\services\sfv_tasks.py                                  
C:\dev\sns emr\backend\app\services\survey_export.py                              
C:\dev\sns emr\backend\app\services\survey_token.py                               
C:\dev\sns emr\backend\app\services\task_auto_complete_engine.py                  
C:\dev\sns emr\backend\app\services\task_benefit_period_linker.py                 
C:\dev\sns emr\backend\app\services\task_completion.py                            
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                   
C:\dev\sns emr\backend\app\services\task_completion_service.py                    
C:\dev\sns emr\backend\app\services\task_engine.py                                
C:\dev\sns emr\backend\app\services\task_generation.py                            
C:\dev\sns emr\backend\app\services\task_notification_engine.py                   
C:\dev\sns emr\backend\app\services\task_overdue_engine.py                        
C:\dev\sns emr\backend\app\services\task_scheduler.py                             
C:\dev\sns emr\backend\app\services\task_service.py                               
C:\dev\sns emr\backend\app\services\task_sla_engine.py                            
C:\dev\sns emr\backend\app\services\tenant_guard.py                               
C:\dev\sns emr\backend\app\services\text_negation_service.py                      
C:\dev\sns emr\backend\app\services\translation_engine.py                         
C:\dev\sns emr\backend\app\services\visit_compliance_guards.py                    
C:\dev\sns emr\backend\app\services\workflow_resolver.py                          
C:\dev\sns emr\backend\app\services\workflow_validation.py                        
C:\dev\sns emr\backend\app\tenancy\context.py                                     
C:\dev\sns emr\backend\app\tenancy\dependencies.py                                
C:\dev\sns emr\backend\app\tenancy\dev_guards.py                                  
C:\dev\sns emr\backend\app\tenancy\guard.py                                       
C:\dev\sns emr\backend\app\tenancy\registry.py                                    
C:\dev\sns emr\backend\app\tenancy\search_path.py                                 
C:\dev\sns emr\backend\app\tenants\loader.py                                      
C:\dev\sns emr\backend\app\utils\drug_alias.py                                    
C:\dev\sns emr\backend\app\utils\med_normalization.py                             
C:\dev\sns emr\backend\app\utils\test_med_normalization.py                        
C:\dev\sns emr\backend\app\utils\time.py                                          




## 3. Episode Evidence Writers and References


Path                                                                              LineNumber Line                                                                
----                                                                              ---------- ----                                                                
C:\dev\sns emr\backend\app\api\patients.py                                               549         "supporting_evidence_summary": (                            
C:\dev\sns emr\backend\app\api\patients.py                                               550             diagnosis.supporting_evidence_summary                   
C:\dev\sns emr\backend\app\models\patient_diagnosis.py                                   234     supporting_evidence_summary = Column(                           
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         38     supporting_evidence_summary: str                                
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        357         supporting_evidence_summary = self._build_evidence_summary( 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        397             supporting_evidence_summary=supporting_evidence_summary,
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        434                     supporting_evidence_summary,                    
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        469                     :supporting_evidence_summary,                   
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        508                 "supporting_evidence_summary": (                    
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        509                     candidate.supporting_evidence_summary           
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        677     def _build_evidence_summary(                                    
C:\dev\sns emr\backend\app\services\eligibility\eligibility_summary_service.py            68         "summary_type": "ELIGIBILITY_EVIDENCE_SUMMARY",             




## 4. Findings Writers and Significant Change References


Path                                                             LineNumber Line                                                                                                      
----                                                             ---------- ----                                                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         16 class FindingCandidate:                                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         18     finding_type: str                                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         26     observed_at: Optional[datetime] = None                                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         27     is_significant_change: bool = False                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         58         inserted_findings = self.save_findings(db, reasoning_record_id, findings)                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         59         significant_changes = self.create_significant_change_events(                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         88     def extract_findings(self, assessment_data: Dict[str, Any]) -> List[FindingCandidate]:                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         90         observed_at = self._observed_at(assessment_data.get("observed_at"))                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         92         findings: List[FindingCandidate] = []                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         93         findings.extend(self._extract_weight_findings(assessment_data, source, observed_at))              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         94         findings.extend(self._extract_mac_findings(assessment_data, source, observed_at))                 
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         95         findings.extend(self._extract_appetite_findings(assessment_data, source, observed_at))            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         96         findings.extend(self._extract_pain_findings(assessment_data, source, observed_at))                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         97         findings.extend(self._extract_functional_findings(assessment_data, source, observed_at))          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         98         findings.extend(self._extract_safety_findings(assessment_data, source, observed_at))              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py         99         findings.extend(self._extract_caregiver_findings(assessment_data, source, observed_at))           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        100         findings.extend(self._extract_respiratory_findings(assessment_data, source, observed_at))         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        101         findings.extend(self._extract_cardiac_findings(assessment_data, source, observed_at))             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        102         findings.extend(self._extract_cognitive_behavior_findings(assessment_data, source, observed_at))  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        103         findings.extend(self._extract_spiritual_findings(assessment_data, source, observed_at))           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        107     def save_findings(                                                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        111         findings: Iterable[FindingCandidate],                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        119                     INSERT INTO findings (                                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        122                         finding_type,                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        130                         observed_at,                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        131                         is_significant_change                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        136                         :finding_type,                                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        144                         :observed_at,                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        145                         :is_significant_change                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        150                         finding_type,                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        153                         is_significant_change                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        159                     "finding_type": finding.finding_type,                                                 
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        167                     "observed_at": finding.observed_at or datetime.now(timezone.utc),                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        168                     "is_significant_change": finding.is_significant_change,                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        176     def create_significant_change_events(                                                                 
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        185             if not finding.get("is_significant_change"):                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        191                     INSERT INTO significant_change_events (                                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        218                     "trigger_type": finding["finding_type"],                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        219                     "description": f"Significant change detected from finding: {finding['finding_type']}",
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        248         finding_types = {finding["finding_type"] for finding in findings}                                 
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        253             required_types = set(rule["required_finding_types"])                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        258             if not required_types.issubset(finding_types):                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        277                 if finding["finding_type"] in required_types                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        305             finding_type = str(row.get("finding_type") or "").lower()                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        308             if finding_type in {                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        444                         f.finding_type,                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        452                         f.observed_at,                                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        453                         f.is_significant_change                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        458                     ORDER BY f.observed_at ASC                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        473                             f.finding_type,                                                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        481                             f.observed_at,                                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        482                             f.is_significant_change                                                       
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        485                           AND f.finding_type IN (                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        493                         ORDER BY f.observed_at ASC                                                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        642                 DELETE FROM significant_change_events                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        720         observed_at: datetime,                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        721     ) -> List[FindingCandidate]:                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        730                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        732                     finding_type="weight_loss",                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        737                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        738                     is_significant_change=True,                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        744                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        746                     finding_type="weight_gain",                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        751                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        761         observed_at: datetime,                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        762     ) -> List[FindingCandidate]:                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        771                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        773                     finding_type="mac_decline",                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        778                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        788         observed_at: datetime,                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        789     ) -> List[FindingCandidate]:                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        793         findings: List[FindingCandidate] = []                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        797                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        799                     finding_type="poor_appetite",                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        804                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        805                     is_significant_change=appetite_decline,                                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        811                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        813                     finding_type="significant_change_appetite",                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        816                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        817                     is_significant_change=True,                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        827         observed_at: datetime,                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        828     ) -> List[FindingCandidate]:                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        832         findings: List[FindingCandidate] = []                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        841                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        843                     finding_type="pain",                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        849                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        850                     is_significant_change=pain_increase,                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        856                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        858                     finding_type="significant_change_pain",                                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        861                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        862                     is_significant_change=True,                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        872                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        874                     finding_type="pain_location",                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        877                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        884                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        886                     finding_type="pain_quality",                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        889                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        900                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        902                     finding_type="pain_cause_category",                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        905                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        916                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        918                     finding_type="pain_cause_text",                                                       
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        921                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        928                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        930                     finding_type="assessment_summary",                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        933                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        940                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        942                     finding_type="nursing_summary",                                                       
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        945                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        955         observed_at: datetime,                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        956     ) -> List[FindingCandidate]:                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        957         findings: List[FindingCandidate] = []                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        961                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        963                     finding_type="weakness",                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        966                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        972                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        974                     finding_type="mobility_decline",                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        977                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        983                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        985                     finding_type="transfer_dependence",                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        988                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        998         observed_at: datetime,                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py        999     ) -> List[FindingCandidate]:                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1006             FindingCandidate(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1008                 finding_type="fall",                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1012                 observed_at=observed_at,                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1013                 is_significant_change=True,                                                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1021         observed_at: datetime,                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1022     ) -> List[FindingCandidate]:                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1023         findings: List[FindingCandidate] = []                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1027                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1029                     finding_type="caregiver_distress",                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1032                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1038                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1040                     finding_type="caregiver_overwhelmed",                                                 
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1043                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1053         observed_at: datetime,                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1054     ) -> List[FindingCandidate]:                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1055         findings: List[FindingCandidate] = []                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1067                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1069                     finding_type="tachypnea",                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1074                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1080                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1082                     finding_type="accessory_muscle_use",                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1085                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1091                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1093                     finding_type="oxygen_increase",                                                       
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1096                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1097                     is_significant_change=True,                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1107         observed_at: datetime,                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1108     ) -> List[FindingCandidate]:                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1109         findings: List[FindingCandidate] = []                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1113                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1115                     finding_type="edema",                                                                 
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1118                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1124                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1126                     finding_type="orthopnea",                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1129                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1139         observed_at: datetime,                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1140     ) -> List[FindingCandidate]:                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1141         findings: List[FindingCandidate] = []                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1145                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1147                     finding_type="cognitive_decline",                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1150                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1151                     is_significant_change=True,                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1157                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1159                     finding_type="behavior_change",                                                       
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1162                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1163                     is_significant_change=True,                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1173         observed_at: datetime,                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1174     ) -> List[FindingCandidate]:                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1175         findings: List[FindingCandidate] = []                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1179                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1181                     finding_type="spiritual_distress",                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1184                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1190                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1192                     finding_type="fear_of_dying",                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1195                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1201                 FindingCandidate(                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1203                     finding_type="hopelessness",                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1206                     observed_at=observed_at,                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1216                 SELECT id, finding_type                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1237                         ARRAY_AGG(c.required_finding_type ORDER BY c.required_finding_type)               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1238                             FILTER (WHERE c.required_finding_type IS NOT NULL),                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1240                     ) AS required_finding_types                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1363     def _observed_at(value: Any) -> datetime:                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1377     def _dedupe_findings(findings: List[FindingCandidate]) -> List[FindingCandidate]:                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1379         result: List[FindingCandidate] = []                                                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py       1384                 finding.finding_type,                                                                     




## 5. Communication Log Bridge Search


Path                                                                              LineNumber Line                                                                                                                     
----                                                                              ---------- ----                                                                                                                     
C:\dev\sns emr\backend\app\api\adr_readiness.py                                           31     fail_count = len(audit.findings)                                                                                     
C:\dev\sns emr\backend\app\api\adr_readiness.py                                           37         top = [f.rule_id for f in audit.findings[:5]]                                                                    
C:\dev\sns emr\backend\app\api\f2f.py                                                    165         "Clinical findings support progression of terminal disease and continued hospice eligibility."                   
C:\dev\sns emr\backend\app\api\visits.py                                                  56     enforce_commlog_for_visit_status_change,                                                                             
C:\dev\sns emr\backend\app\api\visits.py                                                  63 from app.services.clinical_reasoning_engine import ClinicalReasoningEngine                                               
C:\dev\sns emr\backend\app\api\visits.py                                                 145 clinical_reasoning_engine = ClinicalReasoningEngine()                                                                    
C:\dev\sns emr\backend\app\api\visits.py                                                 583                     "Keep ROUTINE_VISIT and document psychosocial findings in the SW routine form."                      
C:\dev\sns emr\backend\app\api\visits.py                                                1982     enforce_commlog_for_visit_status_change(                                                                             
C:\dev\sns emr\backend\app\api\visits.py                                                2823 def _extract_clinical_reasoning_payload_from_notes(                                                                      
C:\dev\sns emr\backend\app\api\visits.py                                                2923         "CLINICAL_REASONING_EXTRACTED_PAYLOAD %s",                                                                       
C:\dev\sns emr\backend\app\api\visits.py                                                2930 def _get_or_create_clinical_reasoning_record_for_visit(                                                                  
C:\dev\sns emr\backend\app\api\visits.py                                                2938             FROM clinical_reasoning_records                                                                              
C:\dev\sns emr\backend\app\api\visits.py                                                2958             INSERT INTO clinical_reasoning_records (                                                                     
C:\dev\sns emr\backend\app\api\visits.py                                                2964                 requires_idg_review                                                                                      
C:\dev\sns emr\backend\app\api\visits.py                                                2986 def _run_clinical_reasoning_for_visit(                                                                                   
C:\dev\sns emr\backend\app\api\visits.py                                                2992     assessment_payload = _extract_clinical_reasoning_payload_from_notes(notes)                                           
C:\dev\sns emr\backend\app\api\visits.py                                                2995         "CLINICAL_REASONING_PAYLOAD_DEBUG visit_id=%s payload_keys=%s payload=%s request_id=%s",                         
C:\dev\sns emr\backend\app\api\visits.py                                                3004             "CLINICAL_REASONING_SKIPPED_EMPTY_PAYLOAD visit_id=%s request_id=%s",                                        
C:\dev\sns emr\backend\app\api\visits.py                                                3010     reasoning_record_id = _get_or_create_clinical_reasoning_record_for_visit(                                            
C:\dev\sns emr\backend\app\api\visits.py                                                3015     result = clinical_reasoning_engine.process_assessment(                                                               
C:\dev\sns emr\backend\app\api\visits.py                                                3039         "CLINICAL_REASONING_COMPLETED visit_id=%s reasoning_record_id=%s result=%s request_id=%s",                       
C:\dev\sns emr\backend\app\api\visits.py                                                3295             "CLINICAL_REASONING_GATE_CHECK visit_id=%s visit_type=%s discipline=%s is_rn=%s note_count=%s request_id=%s",
C:\dev\sns emr\backend\app\api\visits.py                                                3306                 "FINALIZE: BEFORE_CLINICAL_REASONING visit_id=%s request_id=%s",                                         
C:\dev\sns emr\backend\app\api\visits.py                                                3310             _run_clinical_reasoning_for_visit(                                                                           
C:\dev\sns emr\backend\app\api\visits.py                                                3317                 "FINALIZE: AFTER_CLINICAL_REASONING visit_id=%s request_id=%s",                                          
C:\dev\sns emr\backend\app\api\admin\chart_export.py                                     126             "communications_logs",                                                                                       
C:\dev\sns emr\backend\app\api\admin\chart_export.py                                     129             FROM communications_logs                                                                                     
C:\dev\sns emr\backend\app\api\admin\chart_export.py                                     175                 FROM communications_logs                                                                                 
C:\dev\sns emr\backend\app\api\communications_log\router.py                               14 from app.models.communications_log import CommunicationsLog                                                              
C:\dev\sns emr\backend\app\api\communications_log\router.py                               16     CommunicationsLogCreate,                                                                                             
C:\dev\sns emr\backend\app\api\communications_log\router.py                               17     CommunicationsLogRead,                                                                                               
C:\dev\sns emr\backend\app\api\communications_log\router.py                               18     CommunicationsLogAction,                                                                                             
C:\dev\sns emr\backend\app\api\communications_log\router.py                               20 from app.services.communications_log_alerts import create_commlog_alerts                                                 
C:\dev\sns emr\backend\app\api\communications_log\router.py                               21 from app.services.commlog_to_task_bridge import handle_commlog_for_tasks                                                 
C:\dev\sns emr\backend\app\api\communications_log\router.py                              147             "COMMLOG ALERT RECIPIENT RESOLUTION (ASSIGNED USERS) FAILED: %s",                                            
C:\dev\sns emr\backend\app\api\communications_log\router.py                              180             "COMMLOG ALERT RECIPIENT RESOLUTION (ADMINS) FAILED: %s",                                                    
C:\dev\sns emr\backend\app\api\communications_log\router.py                              272     entry: CommunicationsLog,                                                                                            
C:\dev\sns emr\backend\app\api\communications_log\router.py                              298 def _get_commlog_for_patient_scope(                                                                                      
C:\dev\sns emr\backend\app\api\communications_log\router.py                              301     commlog_id: UUID,                                                                                                    
C:\dev\sns emr\backend\app\api\communications_log\router.py                              303 ) -> CommunicationsLog:                                                                                                  
C:\dev\sns emr\backend\app\api\communications_log\router.py                              305         db.query(CommunicationsLog)                                                                                      
C:\dev\sns emr\backend\app\api\communications_log\router.py                              307             CommunicationsLog.id == commlog_id,                                                                          
C:\dev\sns emr\backend\app\api\communications_log\router.py                              308             CommunicationsLog.tenant_id == tenant_id,                                                                    
C:\dev\sns emr\backend\app\api\communications_log\router.py                              323 @router.post("", response_model=CommunicationsLogRead)                                                                   
C:\dev\sns emr\backend\app\api\communications_log\router.py                              325     payload: CommunicationsLogCreate,                                                                                    
C:\dev\sns emr\backend\app\api\communications_log\router.py                              339     entry = CommunicationsLog(                                                                                           
C:\dev\sns emr\backend\app\api\communications_log\router.py                              366             "COMMLOG ALERT RECIPIENTS resolved patient_id=%s tenant_id=%s recipients=%s",                                
C:\dev\sns emr\backend\app\api\communications_log\router.py                              373             create_commlog_alerts(                                                                                       
C:\dev\sns emr\backend\app\api\communications_log\router.py                              377                 commlog_id=entry.id,                                                                                     
C:\dev\sns emr\backend\app\api\communications_log\router.py                              383                 "COMMLOG ALERTS SKIPPED: no recipients found for patient_id=%s tenant_id=%s",                            
C:\dev\sns emr\backend\app\api\communications_log\router.py                              389         logger.error("COMMLOG ALERT FAILURE: %s", e)                                                                     
C:\dev\sns emr\backend\app\api\communications_log\router.py                              395         handle_commlog_for_tasks(db, entry)                                                                              
C:\dev\sns emr\backend\app\api\communications_log\router.py                              397         logger.error("COMMLOG TASK FAILURE: %s", e)                                                                      
C:\dev\sns emr\backend\app\api\communications_log\router.py                              410 @router.get("/patients/", response_model=list[CommunicationsLogRead])                                                    
C:\dev\sns emr\backend\app\api\communications_log\router.py                              432         db.query(CommunicationsLog)                                                                                      
C:\dev\sns emr\backend\app\api\communications_log\router.py                              434             CommunicationsLog.patient_id == patient_id,                                                                  
C:\dev\sns emr\backend\app\api\communications_log\router.py                              435             CommunicationsLog.tenant_id == tenant_id,                                                                    
C:\dev\sns emr\backend\app\api\communications_log\router.py                              437         .order_by(CommunicationsLog.event_time.desc(), CommunicationsLog.created_at.desc())                              
C:\dev\sns emr\backend\app\api\communications_log\router.py                              448 @router.post("/{commlog_id}/acknowledge", response_model=CommunicationsLogRead)                                          
C:\dev\sns emr\backend\app\api\communications_log\router.py                              450     commlog_id: UUID,                                                                                                    
C:\dev\sns emr\backend\app\api\communications_log\router.py                              451     payload: CommunicationsLogAction | None = None,                                                                      
C:\dev\sns emr\backend\app\api\communications_log\router.py                              463     entry = _get_commlog_for_patient_scope(                                                                              
C:\dev\sns emr\backend\app\api\communications_log\router.py                              465         commlog_id=commlog_id,                                                                                           
C:\dev\sns emr\backend\app\api\communications_log\router.py                              503 @router.post("/{commlog_id}/verify", response_model=CommunicationsLogRead)                                               
C:\dev\sns emr\backend\app\api\communications_log\router.py                              505     commlog_id: UUID,                                                                                                    
C:\dev\sns emr\backend\app\api\communications_log\router.py                              506     payload: CommunicationsLogAction | None = None,                                                                      
C:\dev\sns emr\backend\app\api\communications_log\router.py                              518     entry = _get_commlog_for_patient_scope(                                                                              
C:\dev\sns emr\backend\app\api\communications_log\router.py                              520         commlog_id=commlog_id,                                                                                           
C:\dev\sns emr\backend\app\api\communications_log\router.py                              573 @router.post("/{commlog_id}/resolve", response_model=CommunicationsLogRead)                                              
C:\dev\sns emr\backend\app\api\communications_log\router.py                              575     commlog_id: UUID,                                                                                                    
C:\dev\sns emr\backend\app\api\communications_log\router.py                              576     payload: CommunicationsLogAction | None = None,                                                                      
C:\dev\sns emr\backend\app\api\communications_log\router.py                              588     entry = _get_commlog_for_patient_scope(                                                                              
C:\dev\sns emr\backend\app\api\communications_log\router.py                              590         commlog_id=commlog_id,                                                                                           
C:\dev\sns emr\backend\app\api\communications_log\schemas.py                              14 class CommunicationsLogCreate(BaseModel):                                                                                
C:\dev\sns emr\backend\app\api\communications_log\schemas.py                              36 class CommunicationsLogAction(BaseModel):                                                                                
C:\dev\sns emr\backend\app\api\communications_log\schemas.py                              46 class CommunicationsLogRead(BaseModel):                                                                                  
C:\dev\sns emr\backend\app\compliance\cms\evidence.py                                     38     evidence_ref_type: Optional[str] = None,                                                                             
C:\dev\sns emr\backend\app\compliance\cms\evidence.py                                     39     evidence_ref_id: Optional[str] = None,                                                                               
C:\dev\sns emr\backend\app\compliance\cms\evidence.py                                     54     evidence_type = _norm(evidence_ref_type)                                                                             
C:\dev\sns emr\backend\app\compliance\cms\evidence.py                                     55     evidence_id = _norm(evidence_ref_id)                                                                                 
C:\dev\sns emr\backend\app\compliance\cms\evidence.py                                     80                 "(evidence_ref_type and/or evidence_ref_id)."                                                            
C:\dev\sns emr\backend\app\models\communications_log.py                                   11 class CommunicationsLog(Base):                                                                                           
C:\dev\sns emr\backend\app\models\communications_log.py                                   12     __tablename__ = "communications_logs"                                                                                
C:\dev\sns emr\backend\app\models\f2f_encounter.py                                        53     # STRUCTURED CLINICAL FINDINGS (ADR / RECERT DEFENSIBLE)                                                             
C:\dev\sns emr\backend\app\models\icd10_hospice_policy.py                                145     requires_idg_review = Column(                                                                                        
C:\dev\sns emr\backend\app\models\service_coverage_decision.py                            89     evidence_reference_type = Column(                                                                                    
C:\dev\sns emr\backend\app\models\service_coverage_decision.py                            95     evidence_reference_id = Column(                                                                                      
C:\dev\sns emr\backend\app\schemas\adr_audit.py                                           33     findings: List[AdrAuditFinding] = Field(default_factory=list)                                                        
C:\dev\sns emr\backend\app\services\adr_audit_service.py                                  30         self.findings: List[AdrAuditFinding] = []                                                                        
C:\dev\sns emr\backend\app\services\adr_audit_service.py                                  50         self.findings.append(                                                                                            
C:\dev\sns emr\backend\app\services\adr_audit_service.py                                 127             findings=self.findings,                                                                                      
C:\dev\sns emr\backend\app\services\adr_pdf_utils.py                                      40     for f in audit.findings:                                                                                             
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                              123         # Derive urgency from CHHA findings                                                                              
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                   213             "cardiac_findings",                                                                                          
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                   765                     f"Document assessment findings for {_section_label(section)}.",                                      
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                  1466         clarification_items.append("family/facility report of no injury differs from clinician findings")                
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                  1811     if _value_present(section_data.get("findings")):                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          35     - Extract findings from assessment data.                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          36     - Save findings.                                                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          39     - Link interpretations to source findings.                                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          57         findings = self.extract_findings(assessment_data)                                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          58         inserted_findings = self.save_findings(db, reasoning_record_id, findings)                                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          60             db, reasoning_record_id, inserted_findings                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          78             "findings_created": len(inserted_findings),                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          82             "findings": inserted_findings,                                                                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          88     def extract_findings(self, assessment_data: Dict[str, Any]) -> List[FindingCandidate]:                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          92         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          93         findings.extend(self._extract_weight_findings(assessment_data, source, observed_at))                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          94         findings.extend(self._extract_mac_findings(assessment_data, source, observed_at))                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          95         findings.extend(self._extract_appetite_findings(assessment_data, source, observed_at))                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          96         findings.extend(self._extract_pain_findings(assessment_data, source, observed_at))                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          97         findings.extend(self._extract_functional_findings(assessment_data, source, observed_at))                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          98         findings.extend(self._extract_safety_findings(assessment_data, source, observed_at))                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          99         findings.extend(self._extract_caregiver_findings(assessment_data, source, observed_at))                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         100         findings.extend(self._extract_respiratory_findings(assessment_data, source, observed_at))                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         101         findings.extend(self._extract_cardiac_findings(assessment_data, source, observed_at))                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         102         findings.extend(self._extract_cognitive_behavior_findings(assessment_data, source, observed_at))                 
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         103         findings.extend(self._extract_spiritual_findings(assessment_data, source, observed_at))                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         105         return self._dedupe_findings(findings)                                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         107     def save_findings(                                                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         111         findings: Iterable[FindingCandidate],                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         115         for finding in findings:                                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         119                     INSERT INTO findings (                                                                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         180         inserted_findings: List[Dict[str, Any]],                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         184         for finding in inserted_findings:                                                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         229                     UPDATE clinical_reasoning_records                                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         247         findings = self._load_findings(db, reasoning_record_id)                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         248         finding_types = {finding["finding_type"] for finding in findings}                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         276                 for finding in findings                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         280             self._link_interpretation_findings(                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         380                     crr.requires_idg_review,                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         382                 FROM clinical_reasoning_records crr                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         421                     FROM clinical_reasoning_results                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         454                     FROM interpretation_findings inf                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         455                     JOIN findings f                                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         483                         FROM findings f                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         524                         INSERT INTO clinical_reasoning_results (                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         544                         requires_idg_review,                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         573                         :requires_idg_review,                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         610                         "requires_idg_review": bool(record["requires_idg_review"]),                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         628                 DELETE FROM interpretation_findings                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         662                 DELETE FROM findings                                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         672                 UPDATE clinical_reasoning_records                                                                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         676                     requires_idg_review = FALSE,                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         706                 DELETE FROM clinical_reasoning_records                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         716     def _extract_weight_findings(                                                                                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         757     def _extract_mac_findings(                                                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         784     def _extract_appetite_findings(                                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         793         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         796             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         810             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         821         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         823     def _extract_pain_findings(                                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         832         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         840             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         855             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         871             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         883             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         899             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         915             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         927             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         939             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         949         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         951     def _extract_functional_findings(                                                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         957         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         960             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         971             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         982             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         992         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         994     def _extract_safety_findings(                                                                                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1017     def _extract_caregiver_findings(                                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1023         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1026             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1037             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1047         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1049     def _extract_respiratory_findings(                                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1055         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1066             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1079             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1090             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1101         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1103     def _extract_cardiac_findings(                                                                                       
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1109         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1112             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1123             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1133         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1135     def _extract_cognitive_behavior_findings(                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1141         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1144             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1156             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1167         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1169     def _extract_spiritual_findings(                                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1175         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1178             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1189             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1200             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1210         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1212     def _load_findings(self, db: Session, reasoning_record_id: UUID) -> List[Dict[str, Any]]:                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1217                 FROM findings                                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1325     def _link_interpretation_findings(                                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1335                     INSERT INTO interpretation_findings (                                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1377     def _dedupe_findings(findings: List[FindingCandidate]) -> List[FindingCandidate]:                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1381         for finding in findings:                                                                                         
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                             32 def _extract_trigger_type(commlog) -> str | None:                                                                        
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                             36     details = getattr(commlog, "details", None)                                                                          
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                             92     commlog_id,                                                                                                          
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            124             "alert_reason": f"COMM_LOG:{commlog_id}",                                                                    
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            138     commlog,                                                                                                             
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            186             "created_by": getattr(commlog, "created_by", None),                                                          
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            187             "alert_reason": f"COMM_LOG:{commlog.id}",                                                                    
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            192 def handle_commlog_for_tasks(db: Session, commlog) -> None:                                                              
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            204     patient_id = getattr(commlog, "patient_id", None)                                                                    
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            205     tenant_id = getattr(commlog, "tenant_id", None)                                                                      
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            209             "COMMLOG TASK BRIDGE SKIPPED: missing patient_id or tenant_id commlog_id=%s",                                
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            210             getattr(commlog, "id", None),                                                                                
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            214     trigger_type = _extract_trigger_type(commlog)                                                                        
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            218             "COMMLOG TASK BRIDGE SKIPPED: trigger_type=%s commlog_id=%s",                                                
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            220             getattr(commlog, "id", None),                                                                                
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            232             "COMMLOG TASK BRIDGE: no patient clinical assignees found patient_id=%s tenant_id=%s commlog_id=%s",         
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            235             str(getattr(commlog, "id", None)),                                                                           
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            251             commlog_id=commlog.id,                                                                                       
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            261             commlog=commlog,                                                                                             
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            266         "COMMLOG TASK BRIDGE COMPLETE: patient_id=%s tenant_id=%s commlog_id=%s tasks_created=%s",                       
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                            269         str(commlog.id),                                                                                                 
C:\dev\sns emr\backend\app\services\communications_log_alerts.py                          10 def create_commlog_alerts(                                                                                               
C:\dev\sns emr\backend\app\services\communications_log_alerts.py                          15     commlog_id: UUID,                                                                                                    
C:\dev\sns emr\backend\app\services\communications_log_alerts.py                          37                 source_id=commlog_id,                                                                                    
C:\dev\sns emr\backend\app\services\communications_log_service.py                          4 from app.models.communications_log import CommunicationsLog                                                              
C:\dev\sns emr\backend\app\services\communications_log_service.py                          5 from app.services.communications_log_alerts import create_commlog_alerts                                                 
C:\dev\sns emr\backend\app\services\communications_log_service.py                          6 from app.services.commlog_to_task_bridge import handle_commlog_for_tasks                                                 
C:\dev\sns emr\backend\app\services\communications_log_service.py                         21     commlog = CommunicationsLog(                                                                                         
C:\dev\sns emr\backend\app\services\communications_log_service.py                         31     db.add(commlog)                                                                                                      
C:\dev\sns emr\backend\app\services\communications_log_service.py                         38         create_commlog_alerts(                                                                                           
C:\dev\sns emr\backend\app\services\communications_log_service.py                         41             commlog_id=commlog.id,                                                                                       
C:\dev\sns emr\backend\app\services\communications_log_service.py                         52         handle_commlog_for_tasks(db=db, commlog=commlog)                                                                 
C:\dev\sns emr\backend\app\services\communications_log_service.py                         57     db.refresh(commlog)                                                                                                  
C:\dev\sns emr\backend\app\services\communications_log_service.py                         59     return commlog                                                                                                       
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                             53     requires_idg_review: bool                                                                                            
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                            526         requires_idg_review=(                                                                                            
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                            527             policy.requires_idg_review                                                                                   
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         47     requires_idg_review: bool                                                                                            
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         55     Converts clinical_reasoning_results into diagnosis_recommendations.                                                  
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        131                 resolved_requires_idg_review=bool(                                                                       
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        132                     getattr(resolved, "requires_idg_review", False)                                                      
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        177                 FROM clinical_reasoning_results                                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        230                     requires_idg_review,                                                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        233                 FROM clinical_reasoning_results                                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        303         resolved_requires_idg_review: bool,                                                                              
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        352         requires_idg_review = (                                                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        353             resolved_requires_idg_review                                                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        354             or any(bool(row.get("requires_idg_review")) for row in group_results)                                        
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        381             recommendation_source="CLINICAL_REASONING_RESULT",                                                           
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        391                 requires_idg_review=requires_idg_review,                                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        404             requires_idg_review=requires_idg_review,                                                                     
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        441                     requires_idg_review,                                                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        476                     :requires_idg_review,                                                                                
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        517                 "requires_idg_review": candidate.requires_idg_review,                                                    
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        557                 "clinical_reasoning_result_id",                                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        656         requires_idg_review: bool,                                                                                       
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        672         if requires_idg_review:                                                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        726             "Generated from clinical_reasoning_results. "                                                                
C:\dev\sns emr\backend\app\services\visit_compliance_guards.py                             9 from app.models.communications_log import CommunicationsLog                                                              
C:\dev\sns emr\backend\app\services\visit_compliance_guards.py                            12 def enforce_commlog_for_visit_status_change(                                                                             
C:\dev\sns emr\backend\app\services\visit_compliance_guards.py                            49         db.query(CommunicationsLog)                                                                                      
C:\dev\sns emr\backend\app\services\visit_compliance_guards.py                            50         .filter(CommunicationsLog.id == communications_log_id)                                                           




## 6. CHHA Bridge Search


Path                                                                               LineNumber Line                                                                                                                     
----                                                                               ---------- ----                                                                                                                     
C:\dev\sns emr\backend\app\api\adr_readiness.py                                            31     fail_count = len(audit.findings)                                                                                     
C:\dev\sns emr\backend\app\api\adr_readiness.py                                            37         top = [f.rule_id for f in audit.findings[:5]]                                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                10 from app.models.chha_poc import CHHAPOC                                                                                  
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                14     prefix="/chha-pocs",                                                                                                 
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                15     tags=["CHHA Plan of Care"],                                                                                          
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                19 @router.post("/", status_code=status.HTTP_201_CREATED, summary="Create CHHA POC (draft)")                                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                20 def create_chha_poc(                                                                                                     
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                28     poc = CHHAPOC(                                                                                                       
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                42         action="CREATE_CHHA_POC",                                                                                        
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                43         entity_type="chha_poc",                                                                                          
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                52         "chha_poc_id": str(poc.id),                                                                                      
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                59 @router.get("/patient/{patient_id}", summary="List CHHA POCs for a patient")                                             
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                60 def list_chha_pocs_for_patient(                                                                                          
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                63     user: CurrentUser = Depends(require_roles(["RN", "NP", "MD", "CHHA"])),                                              
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                66         db.query(CHHAPOC)                                                                                                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                67         .filter(CHHAPOC.patient_id == patient_id)                                                                        
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                68         .order_by(CHHAPOC.created_at.desc())                                                                             
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                74             "chha_poc_id": str(poc.id),                                                                                  
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                87     "/{chha_poc_id}/finalize",                                                                                           
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                89     summary="Finalize (activate) a CHHA Plan of Care",                                                                   
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                91 def finalize_chha_poc(                                                                                                   
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                92     chha_poc_id: uuid.UUID,                                                                                              
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                96     poc = db.query(CHHAPOC).filter(CHHAPOC.id == chha_poc_id).first()                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                                98         raise HTTPException(status_code=404, detail="CHHA Plan of Care not found")                                       
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               101         raise HTTPException(status_code=400, detail="CHHA Plan of Care is already active")                               
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               104         raise HTTPException(status_code=400, detail="Superseded CHHA Plan of Care cannot be finalized")                  
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               108         db.query(CHHAPOC)                                                                                                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               109         .filter(CHHAPOC.patient_id == poc.patient_id, CHHAPOC.status == "active")                                        
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               126         action="FINALIZE_CHHA_POC",                                                                                      
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               127         entity_type="chha_poc",                                                                                          
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               136         "chha_poc_id": str(poc.id),                                                                                      
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               147     "/{chha_poc_id}/supersede",                                                                                          
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               149     summary="Supersede (retire) an active CHHA Plan of Care",                                                            
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               151 def supersede_chha_poc(                                                                                                  
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               152     chha_poc_id: uuid.UUID,                                                                                              
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               157     poc = db.query(CHHAPOC).filter(CHHAPOC.id == chha_poc_id).first()                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               159         raise HTTPException(status_code=404, detail="CHHA Plan of Care not found")                                       
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               162         raise HTTPException(status_code=400, detail="Only an active CHHA Plan of Care can be superseded")                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               172         action="SUPERSEDE_CHHA_POC",                                                                                     
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               173         entity_type="chha_poc",                                                                                          
C:\dev\sns emr\backend\app\api\chha_pocs.py                                               182         "chha_poc_id": str(poc.id),                                                                                      
C:\dev\sns emr\backend\app\api\f2f.py                                                     165         "Clinical findings support progression of terminal disease and continued hospice eligibility."                   
C:\dev\sns emr\backend\app\api\patients.py                                                183     if user.role in {"CHHA", "VOLUNTEER"}:                                                                               
C:\dev\sns emr\backend\app\api\registry.py                                                 22     chha_pocs,                                                                                                           
C:\dev\sns emr\backend\app\api\registry.py                                                136         chha_pocs.router,                                                                                                
C:\dev\sns emr\backend\app\api\visits.py                                                   41 from app.services.chha_outcome_service import upsert_chha_outcome                                                        
C:\dev\sns emr\backend\app\api\visits.py                                                   63 from app.services.clinical_reasoning_engine import ClinicalReasoningEngine                                               
C:\dev\sns emr\backend\app\api\visits.py                                                   91     "AIDE",                                                                                                              
C:\dev\sns emr\backend\app\api\visits.py                                                  116     "CHHA": "AIDE",                                                                                                      
C:\dev\sns emr\backend\app\api\visits.py                                                  145 clinical_reasoning_engine = ClinicalReasoningEngine()                                                                    
C:\dev\sns emr\backend\app\api\visits.py                                                  197         description="Discipline: RN, LVN, SW, CHAPLAIN, AIDE, MD, NP, PA, ADMINISTRATIVE",                               
C:\dev\sns emr\backend\app\api\visits.py                                                  203         description="Service classification: SN (Skilled Nursing), MSW, CHAPLAIN, AIDE",                                 
C:\dev\sns emr\backend\app\api\visits.py                                                  269             "CHHA": "AIDE",                                                                                              
C:\dev\sns emr\backend\app\api\visits.py                                                  336 class CHHATaskResultItem(BaseModel):                                                                                     
C:\dev\sns emr\backend\app\api\visits.py                                                  347 class CHHAOutcomeUpsertRequest(BaseModel):                                                                               
C:\dev\sns emr\backend\app\api\visits.py                                                  362     task_results: List[CHHATaskResultItem] = Field(default_factory=list)                                                 
C:\dev\sns emr\backend\app\api\visits.py                                                  368         description="LVN, CHHA, MSW, SC, RN, MD, NP, PA",                                                                
C:\dev\sns emr\backend\app\api\visits.py                                                  583                     "Keep ROUTINE_VISIT and document psychosocial findings in the SW routine form."                      
C:\dev\sns emr\backend\app\api\visits.py                                                  860     if key == "CHHA":                                                                                                    
C:\dev\sns emr\backend\app\api\visits.py                                                  862             getattr(patient, "chha_refused", False)                                                                      
C:\dev\sns emr\backend\app\api\visits.py                                                  863             or getattr(patient, "aide_refused", False)                                                                   
C:\dev\sns emr\backend\app\api\visits.py                                                  875     if key == "CHHA":                                                                                                    
C:\dev\sns emr\backend\app\api\visits.py                                                  876         return bool(getattr(patient, "has_chha", False))                                                                 
C:\dev\sns emr\backend\app\api\visits.py                                                  889         List[str] of normalized uppercase targets (e.g. ["LVN", "CHHA"]).                                                
C:\dev\sns emr\backend\app\api\visits.py                                                  950 def _is_chha_supervision_due(                                                                                            
C:\dev\sns emr\backend\app\api\visits.py                                                  956     if not _patient_has_active_staff(patient, "CHHA"):                                                                   
C:\dev\sns emr\backend\app\api\visits.py                                                  959     if _get_patient_refusal_flag(patient, "CHHA"):                                                                       
C:\dev\sns emr\backend\app\api\visits.py                                                  966         target="CHHA",                                                                                                   
C:\dev\sns emr\backend\app\api\visits.py                                                 1039     if _is_chha_supervision_due(                                                                                         
C:\dev\sns emr\backend\app\api\visits.py                                                 1044         targets.append("CHHA")                                                                                           
C:\dev\sns emr\backend\app\api\visits.py                                                 2538 @router.post("/{visit_id}/chha-outcome")                                                                                 
C:\dev\sns emr\backend\app\api\visits.py                                                 2539 def upsert_chha_visit_outcome(                                                                                           
C:\dev\sns emr\backend\app\api\visits.py                                                 2541     payload: CHHAOutcomeUpsertRequest,                                                                                   
C:\dev\sns emr\backend\app\api\visits.py                                                 2572     if discipline not in {"AIDE"}:                                                                                       
C:\dev\sns emr\backend\app\api\visits.py                                                 2575             detail="CHHA outcome can only be recorded for AIDE/CHHA visits",                                             
C:\dev\sns emr\backend\app\api\visits.py                                                 2598         outcome = upsert_chha_outcome(                                                                                   
C:\dev\sns emr\backend\app\api\visits.py                                                 2611             action="UPSERT_CHHA_OUTCOME",                                                                                
C:\dev\sns emr\backend\app\api\visits.py                                                 2633             "CHHA_OUTCOME_SAVE_FAILED",                                                                                  
C:\dev\sns emr\backend\app\api\visits.py                                                 2643             detail=f"CHHA outcome save failed: {exc}",                                                                   
C:\dev\sns emr\backend\app\api\visits.py                                                 2695         "AIDE",                                                                                                          
C:\dev\sns emr\backend\app\api\visits.py                                                 2823 def _extract_clinical_reasoning_payload_from_notes(                                                                      
C:\dev\sns emr\backend\app\api\visits.py                                                 2923         "CLINICAL_REASONING_EXTRACTED_PAYLOAD %s",                                                                       
C:\dev\sns emr\backend\app\api\visits.py                                                 2930 def _get_or_create_clinical_reasoning_record_for_visit(                                                                  
C:\dev\sns emr\backend\app\api\visits.py                                                 2938             FROM clinical_reasoning_records                                                                              
C:\dev\sns emr\backend\app\api\visits.py                                                 2958             INSERT INTO clinical_reasoning_records (                                                                     
C:\dev\sns emr\backend\app\api\visits.py                                                 2964                 requires_idg_review                                                                                      
C:\dev\sns emr\backend\app\api\visits.py                                                 2986 def _run_clinical_reasoning_for_visit(                                                                                   
C:\dev\sns emr\backend\app\api\visits.py                                                 2992     assessment_payload = _extract_clinical_reasoning_payload_from_notes(notes)                                           
C:\dev\sns emr\backend\app\api\visits.py                                                 2995         "CLINICAL_REASONING_PAYLOAD_DEBUG visit_id=%s payload_keys=%s payload=%s request_id=%s",                         
C:\dev\sns emr\backend\app\api\visits.py                                                 3004             "CLINICAL_REASONING_SKIPPED_EMPTY_PAYLOAD visit_id=%s request_id=%s",                                        
C:\dev\sns emr\backend\app\api\visits.py                                                 3010     reasoning_record_id = _get_or_create_clinical_reasoning_record_for_visit(                                            
C:\dev\sns emr\backend\app\api\visits.py                                                 3015     result = clinical_reasoning_engine.process_assessment(                                                               
C:\dev\sns emr\backend\app\api\visits.py                                                 3039         "CLINICAL_REASONING_COMPLETED visit_id=%s reasoning_record_id=%s result=%s request_id=%s",                       
C:\dev\sns emr\backend\app\api\visits.py                                                 3295             "CLINICAL_REASONING_GATE_CHECK visit_id=%s visit_type=%s discipline=%s is_rn=%s note_count=%s request_id=%s",
C:\dev\sns emr\backend\app\api\visits.py                                                 3306                 "FINALIZE: BEFORE_CLINICAL_REASONING visit_id=%s request_id=%s",                                         
C:\dev\sns emr\backend\app\api\visits.py                                                 3310             _run_clinical_reasoning_for_visit(                                                                           
C:\dev\sns emr\backend\app\api\visits.py                                                 3317                 "FINALIZE: AFTER_CLINICAL_REASONING visit_id=%s request_id=%s",                                          
C:\dev\sns emr\backend\app\billing\models\authorization.py                                 53         doc="RN / HHA / PT / OT / ST / MSW",                                                                             
C:\dev\sns emr\backend\app\billing\models\orders_snapshot.py                               51         doc="RN / LVN / HHA / PT / OT / ST / MSW",                                                                       
C:\dev\sns emr\backend\app\billing\models\visit_minutes.py                                 51         doc="RN / LVN / HHA / PT / OT / ST / MSW",                                                                       
C:\dev\sns emr\backend\app\core\authorization.py                                           14     "CHHA",                                                                                                              
C:\dev\sns emr\backend\app\core\authorization.py                                           32     "CHHA",                                                                                                              
C:\dev\sns emr\backend\app\core\authorization.py                                           33     "AIDE",                                                                                                              
C:\dev\sns emr\backend\app\core\authorization.py                                           70     CHHA                                                                                                                 
C:\dev\sns emr\backend\app\core\authorization.py                                           71         CHHA documents CHHA                                                                                              
C:\dev\sns emr\backend\app\core\authorization.py                                          142     # CHHA / AIDE                                                                                                        
C:\dev\sns emr\backend\app\core\authorization.py                                          144     elif visit_type in {"CHHA", "AIDE"}:                                                                                 
C:\dev\sns emr\backend\app\core\authorization.py                                          146             "CHHA",                                                                                                      
C:\dev\sns emr\backend\app\core\authorization.py                                          153                 detail="User not authorized to document CHHA visits",                                                    
C:\dev\sns emr\backend\app\core\visit_types.py                                             15     "CHHA",                                                                                                              
C:\dev\sns emr\backend\app\core\visit_types.py                                             20     "AIDE": "CHHA",                                                                                                      
C:\dev\sns emr\backend\app\core\visit_types.py                                             21     "HHA": "CHHA",                                                                                                       
C:\dev\sns emr\backend\app\core\visit_types.py                                             22     "CNA": "CHHA",                                                                                                       
C:\dev\sns emr\backend\app\core\visit_types.py                                             61     "AIDE",                                                                                                              
C:\dev\sns emr\backend\app\core\visit_types.py                                             62     "HHA",                                                                                                               
C:\dev\sns emr\backend\app\core\visit_types.py                                             75     "HHA": "HHA",                                                                                                        
C:\dev\sns emr\backend\app\core\visit_types.py                                             76     "HOME HEALTH AIDE": "HHA",                                                                                           
C:\dev\sns emr\backend\app\core\visit_types.py                                             77     "HOMEHEALTHAIDE": "HHA",                                                                                             
C:\dev\sns emr\backend\app\core\visit_types.py                                             78     "AID": "AIDE",                                                                                                       
C:\dev\sns emr\backend\app\core\visit_types.py                                             79     "AIDE": "AIDE",                                                                                                      
C:\dev\sns emr\backend\app\core\visit_type_normalizer.py                                   21     "AIDE",                                                                                                              
C:\dev\sns emr\backend\app\core\visit_type_normalizer.py                                   34     "HOME HEALTH AIDE": "AIDE",                                                                                          
C:\dev\sns emr\backend\app\core\visit_type_normalizer.py                                   35     "HHA": "AIDE",                                                                                                       
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                     20     RN_PLUS_CHHA = "RN_PLUS_CHHA"                                                                                        
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                     21     RN_PLUS_LVN_CHHA = "RN_PLUS_LVN_CHHA"                                                                                
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    113     has_chha: bool,                                                                                                      
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    120     chha = bool(has_chha)                                                                                                
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    123     if lvn and chha:                                                                                                     
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    124         return CareModel.RN_PLUS_LVN_CHHA                                                                                
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    129     if chha:                                                                                                             
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    130         return CareModel.RN_PLUS_CHHA                                                                                    
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    137     has_chha: bool,                                                                                                      
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    144     - CHHA                                                                                                               
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    148     return bool(has_chha or has_lvn)                                                                                     
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    193     has_chha: bool,                                                                                                      
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    214           3. RN + CHHA patients                                                                                          
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    215           4. RN + LVN + CHHA patients                                                                                    
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    232     normalized_has_chha = bool(has_chha)                                                                                 
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    239         has_chha=normalized_has_chha,                                                                                    
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    244         has_chha=normalized_has_chha,                                                                                    
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    288     # LVN/CHHA support requires supervisory RN anchor.                                                                   
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                    300                 "ROUTINE with LVN/CHHA support: supervisory RN visit is required to anchor "                             
C:\dev\sns emr\backend\app\domain\visits.py                                                12     "AIDE": "CHHA",                                                                                                      
C:\dev\sns emr\backend\app\domain\visits.py                                                13     "CNA": "CHHA",                                                                                                       
C:\dev\sns emr\backend\app\domain\visits.py                                                14     "HOME HEALTH AIDE": "CHHA",                                                                                          
C:\dev\sns emr\backend\app\domain\visits.py                                                30     "CHHA",                                                                                                              
C:\dev\sns emr\backend\app\domain\forms\discipline_rules.py                                16 SUPPORT_DISCIPLINES = {"CHHA", "AIDE", "VOLUNTEER"}                                                                      
C:\dev\sns emr\backend\app\domain\forms\discipline_rules.py                                35     # MSW / SC / CHHA / other support roles cannot own RN/NP structured modules                                          
C:\dev\sns emr\backend\app\domain\forms\enums.py                                           29     AIDE = "AIDE"                                                                                                        
C:\dev\sns emr\backend\app\domain\forms\enums.py                                           43     HHA = "HHA"                                                                                                          
C:\dev\sns emr\backend\app\domain\forms\form_registry.py                                  127     TaskDiscipline.CHHA: NoteFormFamily.SUPPORT,                                                                         
C:\dev\sns emr\backend\app\domain\forms\form_registry.py                                  196     "AIDE": {                                                                                                            
C:\dev\sns emr\backend\app\domain\forms\form_registry.py                                  199             primary_form="AIDE_VISIT_V1",                                                                                
C:\dev\sns emr\backend\app\domain\forms\form_registry.py                                  259     if d == "AIDE":                                                                                                      
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                         75     "CHHA": "AIDE",                                                                                                      
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                        319     # ✅ AIDE                                                                                                             
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                        321     if d == "AIDE":                                                                                                      
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                        323             return "HHA_VISIT"                                                                                           
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                        326             f"AIDE cannot perform form_type '{f}'"                                                                       
C:\dev\sns emr\backend\app\domain\forms\module_registry.py                                 50         "description": "Care provided / aide support / supportive services"                                              
C:\dev\sns emr\backend\app\models\chha_poc.py                                               6 class CHHAPOC(BaseModel):                                                                                                
C:\dev\sns emr\backend\app\models\chha_poc.py                                               7     __tablename__ = "chha_pocs"                                                                                          
C:\dev\sns emr\backend\app\models\chha_poc.py                                              28             raise ValueError("CHHA POC already finalized")                                                               
C:\dev\sns emr\backend\app\models\chha_visit_outcome.py                                    13 class CHHAVisitOutcome(Base):                                                                                            
C:\dev\sns emr\backend\app\models\chha_visit_outcome.py                                    14     __tablename__ = "chha_visit_outcomes"                                                                                
C:\dev\sns emr\backend\app\models\chha_visit_outcome.py                                    45     visit = relationship("Visit", backref="chha_outcome")                                                                
C:\dev\sns emr\backend\app\models\chha_visit_outcome.py                                    47         "CHHAVisitTaskResult",                                                                                           
C:\dev\sns emr\backend\app\models\chha_visit_outcome.py                                    53         UniqueConstraint("visit_id", name="uq_chha_visit_outcomes_visit_id"),                                            
C:\dev\sns emr\backend\app\models\chha_visit_task_result.py                                13 class CHHAVisitTaskResult(Base):                                                                                         
C:\dev\sns emr\backend\app\models\chha_visit_task_result.py                                14     __tablename__ = "chha_visit_task_results"                                                                            
C:\dev\sns emr\backend\app\models\chha_visit_task_result.py                                17     outcome_id = Column(UUID(as_uuid=True), ForeignKey("chha_visit_outcomes.id"), nullable=False, index=True)            
C:\dev\sns emr\backend\app\models\chha_visit_task_result.py                                36     outcome = relationship("CHHAVisitOutcome", back_populates="task_results")                                            
C:\dev\sns emr\backend\app\models\enums.py                                                 67     AIDE_REOFFER = "AIDE_REOFFER"                                                                                        
C:\dev\sns emr\backend\app\models\enums.py                                                119     CHHA = "CHHA"                                                                                                        
C:\dev\sns emr\backend\app\models\enums.py                                                129     AIDE = "AIDE"                                                                                                        
C:\dev\sns emr\backend\app\models\enums.py                                                177     CHHA = "CHHA"                                                                                                        
C:\dev\sns emr\backend\app\models\enums.py                                                178     AIDE = "AIDE"                                                                                                        
C:\dev\sns emr\backend\app\models\f2f_encounter.py                                         53     # STRUCTURED CLINICAL FINDINGS (ADR / RECERT DEFENSIBLE)                                                             
C:\dev\sns emr\backend\app\models\icd10_hospice_policy.py                                 145     requires_idg_review = Column(                                                                                        
C:\dev\sns emr\backend\app\models\poc.py                                                  357             "discipline IN ('RN', 'MSW', 'SC', 'LVN', 'HHA', 'MD', 'IDG', 'OTHER')",                                     
C:\dev\sns emr\backend\app\models\visit.py                                                186     chha_poc_id = Column(UUID(as_uuid=True), nullable=True, index=True)                                                  
C:\dev\sns emr\backend\app\models\__init__.py                                              57 # ✅ CHHA DOMAIN                                                                                                          
C:\dev\sns emr\backend\app\models\__init__.py                                              60 from app.models.chha_visit_outcome import CHHAVisitOutcome                                                               
C:\dev\sns emr\backend\app\models\__init__.py                                              61 from app.models.chha_visit_task_result import CHHAVisitTaskResult                                                        
C:\dev\sns emr\backend\app\schemas\adr_audit.py                                            33     findings: List[AdrAuditFinding] = Field(default_factory=list)                                                        
C:\dev\sns emr\backend\app\schemas\translation.py                                         104 class CHHAObservations(BaseModel):                                                                                       
C:\dev\sns emr\backend\app\services\adr_audit_service.py                                   30         self.findings: List[AdrAuditFinding] = []                                                                        
C:\dev\sns emr\backend\app\services\adr_audit_service.py                                   50         self.findings.append(                                                                                            
C:\dev\sns emr\backend\app\services\adr_audit_service.py                                  127             findings=self.findings,                                                                                      
C:\dev\sns emr\backend\app\services\adr_pdf_utils.py                                       40     for f in audit.findings:                                                                                             
C:\dev\sns emr\backend\app\services\care_model_service.py                                  43         has_chha=bool(getattr(patient, "has_chha", False)),                                                              
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                13 from app.models.chha_visit_outcome import CHHAVisitOutcome                                                               
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                14 from app.models.chha_visit_task_result import CHHAVisitTaskResult                                                        
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                17 def upsert_chha_outcome(                                                                                                 
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                23 ) -> CHHAVisitOutcome:                                                                                                   
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                25     Upserts structured CHHA outcome documentation for a single visit.                                                    
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                28     - Valid only for CHHA/AIDE visits                                                                                    
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                31     - Creates or updates one RN follow-up task per CHHA visit when:                                                      
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                41     if visit_type not in {"AIDE", "CHHA"} and visit_discipline not in {"AIDE", "CHHA"}:                                  
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                44             detail="CHHA outcome can only be recorded for AIDE/CHHA visits",                                             
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                48         db.query(CHHAVisitOutcome)                                                                                       
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                49         .filter(CHHAVisitOutcome.visit_id == visit.id)                                                                   
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                56         outcome = CHHAVisitOutcome(                                                                                      
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                68     # Update visit-level CHHA outcome                                                                                    
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                90     db.query(CHHAVisitTaskResult).filter(                                                                                
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                91         CHHAVisitTaskResult.outcome_id == outcome.id                                                                     
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                                96             CHHAVisitTaskResult(                                                                                         
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                               123         # Derive urgency from CHHA findings                                                                              
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                               155             query = query.filter(Task.alert_reason == "CHHA_OUTCOME_ALERT")                                              
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                               176                 existing.alert_reason = "CHHA_OUTCOME_ALERT"                                                             
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                               232                 task.alert_reason = "CHHA_OUTCOME_ALERT"                                                                 
C:\dev\sns emr\backend\app\services\clinical_discipline_mapping.py                         13     "CHHA": NOTE_CATEGORY_CLINICAL,                                                                                      
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                     43 DISCIPLINES_ALLOWED = {"RN", "LVN", "MSW", "SC", "HHA", "CHHA", "MD", "NP"}                                              
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                    213             "cardiac_findings",                                                                                          
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                    765                     f"Document assessment findings for {_section_label(section)}.",                                      
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                   1382     if discipline in {"HHA", "CHHA"}:                                                                                    
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                   1385             warnings.append("hha_note_missing_adl_observation")                                                          
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                   1466         clarification_items.append("family/facility report of no injury differs from clinician findings")                
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                   1811     if _value_present(section_data.get("findings")):                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           35     - Extract findings from assessment data.                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           36     - Save findings.                                                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           39     - Link interpretations to source findings.                                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           57         findings = self.extract_findings(assessment_data)                                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           58         inserted_findings = self.save_findings(db, reasoning_record_id, findings)                                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           60             db, reasoning_record_id, inserted_findings                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           78             "findings_created": len(inserted_findings),                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           82             "findings": inserted_findings,                                                                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           88     def extract_findings(self, assessment_data: Dict[str, Any]) -> List[FindingCandidate]:                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           92         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           93         findings.extend(self._extract_weight_findings(assessment_data, source, observed_at))                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           94         findings.extend(self._extract_mac_findings(assessment_data, source, observed_at))                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           95         findings.extend(self._extract_appetite_findings(assessment_data, source, observed_at))                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           96         findings.extend(self._extract_pain_findings(assessment_data, source, observed_at))                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           97         findings.extend(self._extract_functional_findings(assessment_data, source, observed_at))                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           98         findings.extend(self._extract_safety_findings(assessment_data, source, observed_at))                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                           99         findings.extend(self._extract_caregiver_findings(assessment_data, source, observed_at))                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          100         findings.extend(self._extract_respiratory_findings(assessment_data, source, observed_at))                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          101         findings.extend(self._extract_cardiac_findings(assessment_data, source, observed_at))                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          102         findings.extend(self._extract_cognitive_behavior_findings(assessment_data, source, observed_at))                 
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          103         findings.extend(self._extract_spiritual_findings(assessment_data, source, observed_at))                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          105         return self._dedupe_findings(findings)                                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          107     def save_findings(                                                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          111         findings: Iterable[FindingCandidate],                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          115         for finding in findings:                                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          119                     INSERT INTO findings (                                                                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          180         inserted_findings: List[Dict[str, Any]],                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          184         for finding in inserted_findings:                                                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          229                     UPDATE clinical_reasoning_records                                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          247         findings = self._load_findings(db, reasoning_record_id)                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          248         finding_types = {finding["finding_type"] for finding in findings}                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          276                 for finding in findings                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          280             self._link_interpretation_findings(                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          380                     crr.requires_idg_review,                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          382                 FROM clinical_reasoning_records crr                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          421                     FROM clinical_reasoning_results                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          454                     FROM interpretation_findings inf                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          455                     JOIN findings f                                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          483                         FROM findings f                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          524                         INSERT INTO clinical_reasoning_results (                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          544                         requires_idg_review,                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          573                         :requires_idg_review,                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          610                         "requires_idg_review": bool(record["requires_idg_review"]),                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          628                 DELETE FROM interpretation_findings                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          662                 DELETE FROM findings                                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          672                 UPDATE clinical_reasoning_records                                                                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          676                     requires_idg_review = FALSE,                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          706                 DELETE FROM clinical_reasoning_records                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          716     def _extract_weight_findings(                                                                                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          757     def _extract_mac_findings(                                                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          784     def _extract_appetite_findings(                                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          793         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          796             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          810             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          821         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          823     def _extract_pain_findings(                                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          832         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          840             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          855             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          871             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          883             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          899             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          915             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          927             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          939             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          949         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          951     def _extract_functional_findings(                                                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          957         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          960             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          971             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          982             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          992         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          994     def _extract_safety_findings(                                                                                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1017     def _extract_caregiver_findings(                                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1023         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1026             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1037             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1047         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1049     def _extract_respiratory_findings(                                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1055         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1066             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1079             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1090             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1101         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1103     def _extract_cardiac_findings(                                                                                       
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1109         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1112             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1123             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1133         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1135     def _extract_cognitive_behavior_findings(                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1141         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1144             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1156             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1167         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1169     def _extract_spiritual_findings(                                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1175         findings: List[FindingCandidate] = []                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1178             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1189             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1200             findings.append(                                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1210         return findings                                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1212     def _load_findings(self, db: Session, reasoning_record_id: UUID) -> List[Dict[str, Any]]:                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1217                 FROM findings                                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1325     def _link_interpretation_findings(                                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1335                     INSERT INTO interpretation_findings (                                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1377     def _dedupe_findings(findings: List[FindingCandidate]) -> List[FindingCandidate]:                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         1381         for finding in findings:                                                                                         
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                              29 CLINICAL_DISCIPLINES = {"RN", "LVN", "MSW", "BSW", "LCSW", "SC", "CHHA"}                                                 
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                              72                   'CHHA'::tasks_discipline_enum                                                                          
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                              53     requires_idg_review: bool                                                                                            
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                             526         requires_idg_review=(                                                                                            
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                             527             policy.requires_idg_review                                                                                   
C:\dev\sns emr\backend\app\services\poc_generation_service.py                             309             _intervention("HHA", "Assist with hygiene and skin protection measures within aide plan of care."),          
C:\dev\sns emr\backend\app\services\poc_generation_service.py                             449             _intervention("HHA", "Assist with personal care needs according to aide plan of care when ordered."),        
C:\dev\sns emr\backend\app\services\poc_service.py                                         51 ALLOWED_DISCIPLINES = {"RN", "MSW", "SC", "LVN", "HHA", "MD", "IDG", "OTHER"}                                            
C:\dev\sns emr\backend\app\services\poc_service.py                                        545                                 "discipline": "RN|MSW|SC|LVN|HHA|MD|IDG|OTHER",                                          
C:\dev\sns emr\backend\app\services\poc_task_service.py                                   319         has_chha=bool(getattr(patient, "has_chha", False)),                                                              
C:\dev\sns emr\backend\app\services\poc_update_automation.py                              227         has_chha=getattr(patient, "has_chha", False),                                                                    
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py          47     requires_idg_review: bool                                                                                            
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py          55     Converts clinical_reasoning_results into diagnosis_recommendations.                                                  
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         131                 resolved_requires_idg_review=bool(                                                                       
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         132                     getattr(resolved, "requires_idg_review", False)                                                      
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         177                 FROM clinical_reasoning_results                                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         230                     requires_idg_review,                                                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         233                 FROM clinical_reasoning_results                                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         303         resolved_requires_idg_review: bool,                                                                              
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         352         requires_idg_review = (                                                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         353             resolved_requires_idg_review                                                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         354             or any(bool(row.get("requires_idg_review")) for row in group_results)                                        
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         381             recommendation_source="CLINICAL_REASONING_RESULT",                                                           
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         391                 requires_idg_review=requires_idg_review,                                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         404             requires_idg_review=requires_idg_review,                                                                     
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         441                     requires_idg_review,                                                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         476                     :requires_idg_review,                                                                                
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         517                 "requires_idg_review": candidate.requires_idg_review,                                                    
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         557                 "clinical_reasoning_result_id",                                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         656         requires_idg_review: bool,                                                                                       
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         672         if requires_idg_review:                                                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         726             "Generated from clinical_reasoning_results. "                                                                
C:\dev\sns emr\backend\app\services\refusal_engine.py                                      29     "AIDE",                                                                                                              
C:\dev\sns emr\backend\app\services\refusal_engine.py                                      30     "CHHA",                                                                                                              
C:\dev\sns emr\backend\app\services\refusal_engine.py                                      31     "HHA",                                                                                                               
C:\dev\sns emr\backend\app\services\refusal_engine.py                                      52     "AIDE",                                                                                                              
C:\dev\sns emr\backend\app\services\refusal_engine.py                                      67     if discipline in {"HHA", "CHHA", "AIDE"}:                                                                            
C:\dev\sns emr\backend\app\services\refusal_engine.py                                      68         return "AIDE"                                                                                                    
C:\dev\sns emr\backend\app\services\refusal_engine.py                                      78     if discipline == "AIDE":                                                                                             
C:\dev\sns emr\backend\app\services\refusal_engine.py                                      79         return TaskType.AIDE_REOFFER                                                                                     
C:\dev\sns emr\backend\app\services\refusal_engine.py                                     203     if canonical_discipline in {"SW", "CHAPLAIN", "AIDE", "LVN"}:                                                        
C:\dev\sns emr\backend\app\services\admission\admission_status_engine.py                  216                 "CHHA_TASKS",                                                                                            
C:\dev\sns emr\backend\app\services\admission\admission_task_generation_service.py         71         chha_ordered: bool = False,                                                                                      
C:\dev\sns emr\backend\app\services\admission\admission_task_generation_service.py         94                 chha_ordered=chha_ordered,                                                                               
C:\dev\sns emr\backend\app\services\admission\admission_task_generation_service.py        298         chha_ordered: bool,                                                                                              
C:\dev\sns emr\backend\app\services\admission\admission_task_generation_service.py        316         if spec.condition == "chha_ordered":                                                                             
C:\dev\sns emr\backend\app\services\admission\admission_task_generation_service.py        317             return chha_ordered                                                                                          
C:\dev\sns emr\backend\app\services\admission\admission_workflow_service.py               136                 chha_ordered=getattr(                                                                                    
C:\dev\sns emr\backend\app\services\admission\admission_workflow_service.py               138                     "chha_ordered",                                                                                      
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                   42         "CHHA_TASKS",                                                                                                    
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                   62         chha_ordered: bool = False,                                                                                      
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                   94                 chha_ordered=chha_ordered,                                                                               
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                  111         chha_ordered: bool = False,                                                                                      
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                  124                 chha_ordered=chha_ordered,                                                                               
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                  144         chha_ordered: bool = False,                                                                                      
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                  156             chha_ordered=chha_ordered,                                                                                   
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                  171         chha_ordered: bool = False,                                                                                      
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                  184             chha_ordered=chha_ordered,                                                                                   
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                  295         chha_ordered: bool,                                                                                              
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                  326         if chha_ordered:                                                                                                 
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                  329                     "CHHA_TASKS",                                                                                        
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                  330                     "CHHA_POC",                                                                                          
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                  331                     "CHHA_VISIT_DOCUMENTATION",                                                                          
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                  332                     "CHHA_FREQUENCY_TASKS",                                                                              




## 7. IDG Evidence Bridge Search


Path                                                                              LineNumber Line                                                                                                     
----                                                                              ---------- ----                                                                                                     
C:\dev\sns emr\backend\app\api\adr_readiness.py                                           31     fail_count = len(audit.findings)                                                                     
C:\dev\sns emr\backend\app\api\adr_readiness.py                                           37         top = [f.rule_id for f in audit.findings[:5]]                                                    
C:\dev\sns emr\backend\app\api\compliance.py                                               9 from app.models.idg_review import IDGReview                                                              
C:\dev\sns emr\backend\app\api\compliance.py                                              98                 db.query(IDGReview)                                                                      
C:\dev\sns emr\backend\app\api\compliance.py                                              99                 .filter(IDGReview.patient_id == p.id)                                                    
C:\dev\sns emr\backend\app\api\compliance.py                                             100                 .filter(IDGReview.review_date <= as_of)                                                  
C:\dev\sns emr\backend\app\api\compliance.py                                             101                 .order_by(IDGReview.review_date.desc())                                                  
C:\dev\sns emr\backend\app\api\f2f.py                                                    165         "Clinical findings support progression of terminal disease and continued hospice eligibility."   
C:\dev\sns emr\backend\app\api\notes.py                                                  254     if not note.idg_review_id:                                                                           
C:\dev\sns emr\backend\app\api\notes.py                                                  259         idg_review_id=note.idg_review_id,                                                                
C:\dev\sns emr\backend\app\api\patients.py                                               527         "idg_meeting_id": (                                                                              
C:\dev\sns emr\backend\app\api\patients.py                                               528             str(diagnosis.idg_meeting_id)                                                                
C:\dev\sns emr\backend\app\api\patients.py                                               529             if diagnosis.idg_meeting_id                                                                  
C:\dev\sns emr\backend\app\api\visits.py                                                 583                     "Keep ROUTINE_VISIT and document psychosocial findings in the SW routine form."      
C:\dev\sns emr\backend\app\api\visits.py                                                2964                 requires_idg_review                                                                      
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                    131     idg_review_id: Optional[UUID] = None                                                                 
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                    156     idg_review_id: Optional[UUID] = None                                                                 
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                    178     idg_review_id: Optional[UUID] = None                                                                 
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                    251     idg_review_id: Optional[UUID] = None,                                                                
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                    265             idg_review_id=idg_review_id,                                                                 
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                    362         idg_review_id=payload.idg_review_id,                                                             
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                    442             idg_review_id=version.idg_review_id,                                                         
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                    506             idg_review_id=v.idg_review_id,                                                               
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                    564         idg_review_id=version.idg_review_id,                                                             
C:\dev\sns emr\backend\app\models\assessment_discrepancy.py                               32     resolved_in_idg_meeting_id = Column(UUID(as_uuid=True), nullable=True)                               
C:\dev\sns emr\backend\app\models\document_idg_resolution.py                              30             "idg_review_id",                                                                             
C:\dev\sns emr\backend\app\models\document_idg_resolution.py                              31             name="uq_document_idg_review_resolution",                                                    
C:\dev\sns emr\backend\app\models\document_idg_resolution.py                              56     idg_review_id = Column(                                                                              
C:\dev\sns emr\backend\app\models\document_idg_resolution.py                              58         ForeignKey("idg_reviews.id"),                                                                    
C:\dev\sns emr\backend\app\models\enums.py                                                59     IDG_REVIEW = "IDG_REVIEW"                                                                            
C:\dev\sns emr\backend\app\models\enums.py                                                94     IDG_REVIEW = "IDG_REVIEW"                                                                            
C:\dev\sns emr\backend\app\models\enums.py                                               243     IDG_REVIEW = "IDG_REVIEW"                                                                            
C:\dev\sns emr\backend\app\models\f2f_encounter.py                                        53     # STRUCTURED CLINICAL FINDINGS (ADR / RECERT DEFENSIBLE)                                             
C:\dev\sns emr\backend\app\models\icd10_hospice_policy.py                                145     requires_idg_review = Column(                                                                        
C:\dev\sns emr\backend\app\models\idg_attendee.py                                         26             "idg_review_id",                                                                             
C:\dev\sns emr\backend\app\models\idg_attendee.py                                         31         Index("ix_idg_attendees_review", "idg_review_id"),                                               
C:\dev\sns emr\backend\app\models\idg_attendee.py                                         50     idg_review_id = Column(                                                                              
C:\dev\sns emr\backend\app\models\idg_attendee.py                                         52         ForeignKey("idg_reviews.id"),                                                                    
C:\dev\sns emr\backend\app\models\idg_justification.py                                    49     idg_review_id = Column(                                                                              
C:\dev\sns emr\backend\app\models\idg_justification.py                                    51         ForeignKey("idg_reviews.id"),                                                                    
C:\dev\sns emr\backend\app\models\idg_md_attestation.py                                   29         UniqueConstraint("idg_review_id", name="uq_idg_md_attestation_review"),                          
C:\dev\sns emr\backend\app\models\idg_md_attestation.py                                   44     idg_review_id = Column(                                                                              
C:\dev\sns emr\backend\app\models\idg_md_attestation.py                                   46         ForeignKey("idg_reviews.id"),                                                                    
C:\dev\sns emr\backend\app\models\idg_meeting.py                                          32     __tablename__ = "idg_meetings"                                                                       
C:\dev\sns emr\backend\app\models\idg_meeting.py                                          39             name="uq_idg_meeting_patient_date",                                                          
C:\dev\sns emr\backend\app\models\idg_note.py                                             19 class IDGNote(Base):                                                                                     
C:\dev\sns emr\backend\app\models\idg_note.py                                             38             "idg_review_id",                                                                             
C:\dev\sns emr\backend\app\models\idg_note.py                                             69     idg_review_id = Column(                                                                              
C:\dev\sns emr\backend\app\models\idg_note.py                                             71         ForeignKey("idg_reviews.id"),                                                                    
C:\dev\sns emr\backend\app\models\idg_review.py                                            1 # app/models/idg_review.py                                                                               
C:\dev\sns emr\backend\app\models\idg_review.py                                           22 class IDGReview(Base):                                                                                   
C:\dev\sns emr\backend\app\models\idg_review.py                                           38     __tablename__ = "idg_reviews"                                                                        
C:\dev\sns emr\backend\app\models\idg_review.py                                           45             name="uq_idg_review_patient_bp_date",                                                        
C:\dev\sns emr\backend\app\models\idg_review.py                                           48             "ix_idg_reviews_patient_bp",                                                                 
C:\dev\sns emr\backend\app\models\idg_review.py                                           53             "ix_idg_reviews_review_date",                                                                
C:\dev\sns emr\backend\app\models\idg_review.py                                           77     idg_meeting_id = Column(                                                                             
C:\dev\sns emr\backend\app\models\idg_review.py                                           79         ForeignKey("idg_meetings.id"),                                                                   
C:\dev\sns emr\backend\app\models\idg_signature.py                                        29             "idg_meeting_id",                                                                            
C:\dev\sns emr\backend\app\models\idg_signature.py                                        47     idg_meeting_id = Column(                                                                             
C:\dev\sns emr\backend\app\models\idg_signature.py                                        49         ForeignKey("idg_meetings.id"),                                                                   
C:\dev\sns emr\backend\app\models\idg_signature.py                                        54     idg_review_id = Column(                                                                              
C:\dev\sns emr\backend\app\models\idg_signature.py                                        56         ForeignKey("idg_reviews.id"),                                                                    
C:\dev\sns emr\backend\app\models\idg_signature_tracker.py                                17     idg_review_id,                                                                                       
C:\dev\sns emr\backend\app\models\idg_signature_tracker.py                                22         .filter(IDGAttendee.idg_review_id == idg_review_id)                                              
C:\dev\sns emr\backend\app\models\idg_signature_tracker.py                                34     idg_review_id,                                                                                       
C:\dev\sns emr\backend\app\models\idg_signature_tracker.py                                37     attendees = get_idg_attendees(db, idg_review_id=idg_review_id)                                       
C:\dev\sns emr\backend\app\models\idg_signature_tracker.py                                49     idg_review_id,                                                                                       
C:\dev\sns emr\backend\app\models\idg_signature_tracker.py                                52     attendees = get_idg_attendees(db, idg_review_id=idg_review_id)                                       
C:\dev\sns emr\backend\app\models\idg_signature_tracker.py                                64     idg_review_id,                                                                                       
C:\dev\sns emr\backend\app\models\idg_signature_tracker.py                                67     attendees = get_idg_attendees(db, idg_review_id=idg_review_id)                                       
C:\dev\sns emr\backend\app\models\idg_signature_tracker.py                                91     idg_review_id,                                                                                       
C:\dev\sns emr\backend\app\models\idg_signature_tracker.py                                94     attendees = get_idg_attendees(db, idg_review_id=idg_review_id)                                       
C:\dev\sns emr\backend\app\models\patient_diagnosis.py                                   186     idg_meeting_id = Column(                                                                             
C:\dev\sns emr\backend\app\models\patient_diagnosis.py                                   378             "ix_patient_diagnoses_idg_meeting_id",                                                       
C:\dev\sns emr\backend\app\models\patient_diagnosis.py                                   379             "idg_meeting_id",                                                                            
C:\dev\sns emr\backend\app\models\patient_diagnosis.py                                   399             "ix_patient_diagnoses_idg_review",                                                           
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                                 57         Index("ix_pocv_idg_review_id", "idg_review_id"),                                                 
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                                122     idg_review_id = Column(                                                                              
C:\dev\sns emr\backend\app\models\__init__.py                                             80 from app.models.idg_meeting import IDGMeeting                                                            
C:\dev\sns emr\backend\app\models\__init__.py                                             81 from app.models.idg_review import IDGReview                                                              
C:\dev\sns emr\backend\app\models\__init__.py                                             82 from app.models.idg_note import IDGNote                                                                  
C:\dev\sns emr\backend\app\schemas\adr_audit.py                                           33     findings: List[AdrAuditFinding] = Field(default_factory=list)                                        
C:\dev\sns emr\backend\app\services\admission_authorization_service.py                    31 TASK_IDG_REVIEW = "IDG_REVIEW"                                                                           
C:\dev\sns emr\backend\app\services\admission_authorization_service.py                   327     Used for recurring obligations like IDG_REVIEW.                                                      
C:\dev\sns emr\backend\app\services\admission_authorization_service.py                   537     admission_basis = _required_enum_member(TaskRegulatoryBasis, ["IDG_REVIEW", "POC_UPDATE"])           
C:\dev\sns emr\backend\app\services\admission_authorization_service.py                   601     idg_type = _optional_enum_member(TaskType, [TASK_IDG_REVIEW])                                        
C:\dev\sns emr\backend\app\services\admission_authorization_service.py                   604         idg_basis = _required_enum_member(TaskRegulatoryBasis, ["IDG_REVIEW"])                           
C:\dev\sns emr\backend\app\services\adr_audit_service.py                                  30         self.findings: List[AdrAuditFinding] = []                                                        
C:\dev\sns emr\backend\app\services\adr_audit_service.py                                  50         self.findings.append(                                                                            
C:\dev\sns emr\backend\app\services\adr_audit_service.py                                 127             findings=self.findings,                                                                      
C:\dev\sns emr\backend\app\services\adr_pdf_utils.py                                      40     for f in audit.findings:                                                                             
C:\dev\sns emr\backend\app\services\adr_schema_map.py                                    134     TableBinding(table="idg_meetings", columns={                                                         
C:\dev\sns emr\backend\app\services\benefit_period_service.py                            138         # 9. Seed IDG_REVIEW task for the new BP                                                         
C:\dev\sns emr\backend\app\services\benefit_period_service.py                            144             task_type=TaskType.IDG_REVIEW,                                                               
C:\dev\sns emr\backend\app\services\benefit_period_service.py                            147             regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,                                             
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                              123         # Derive urgency from CHHA findings                                                              
C:\dev\sns emr\backend\app\services\clinical_note_service.py                             884     if not getattr(note, "idg_review_id", None):                                                         
C:\dev\sns emr\backend\app\services\clinical_note_service.py                             889         idg_review_id=note.idg_review_id,                                                                
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                   213             "cardiac_findings",                                                                          
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                   765                     f"Document assessment findings for {_section_label(section)}.",                      
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                  1466         clarification_items.append("family/facility report of no injury differs from clinician findings")
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py                  1811     if _value_present(section_data.get("findings")):                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          35     - Extract findings from assessment data.                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          36     - Save findings.                                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          39     - Link interpretations to source findings.                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          57         findings = self.extract_findings(assessment_data)                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          58         inserted_findings = self.save_findings(db, reasoning_record_id, findings)                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          60             db, reasoning_record_id, inserted_findings                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          78             "findings_created": len(inserted_findings),                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          82             "findings": inserted_findings,                                                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          88     def extract_findings(self, assessment_data: Dict[str, Any]) -> List[FindingCandidate]:               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          92         findings: List[FindingCandidate] = []                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          93         findings.extend(self._extract_weight_findings(assessment_data, source, observed_at))             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          94         findings.extend(self._extract_mac_findings(assessment_data, source, observed_at))                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          95         findings.extend(self._extract_appetite_findings(assessment_data, source, observed_at))           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          96         findings.extend(self._extract_pain_findings(assessment_data, source, observed_at))               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          97         findings.extend(self._extract_functional_findings(assessment_data, source, observed_at))         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          98         findings.extend(self._extract_safety_findings(assessment_data, source, observed_at))             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                          99         findings.extend(self._extract_caregiver_findings(assessment_data, source, observed_at))          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         100         findings.extend(self._extract_respiratory_findings(assessment_data, source, observed_at))        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         101         findings.extend(self._extract_cardiac_findings(assessment_data, source, observed_at))            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         102         findings.extend(self._extract_cognitive_behavior_findings(assessment_data, source, observed_at)) 
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         103         findings.extend(self._extract_spiritual_findings(assessment_data, source, observed_at))          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         105         return self._dedupe_findings(findings)                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         107     def save_findings(                                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         111         findings: Iterable[FindingCandidate],                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         115         for finding in findings:                                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         119                     INSERT INTO findings (                                                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         180         inserted_findings: List[Dict[str, Any]],                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         184         for finding in inserted_findings:                                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         247         findings = self._load_findings(db, reasoning_record_id)                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         248         finding_types = {finding["finding_type"] for finding in findings}                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         276                 for finding in findings                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         280             self._link_interpretation_findings(                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         380                     crr.requires_idg_review,                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         421                     FROM clinical_reasoning_results                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         454                     FROM interpretation_findings inf                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         455                     JOIN findings f                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         483                         FROM findings f                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         524                         INSERT INTO clinical_reasoning_results (                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         544                         requires_idg_review,                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         573                         :requires_idg_review,                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         610                         "requires_idg_review": bool(record["requires_idg_review"]),                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         628                 DELETE FROM interpretation_findings                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         662                 DELETE FROM findings                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         676                     requires_idg_review = FALSE,                                                         
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         716     def _extract_weight_findings(                                                                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         757     def _extract_mac_findings(                                                                           
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         784     def _extract_appetite_findings(                                                                      
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         793         findings: List[FindingCandidate] = []                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         796             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         810             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         821         return findings                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         823     def _extract_pain_findings(                                                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         832         findings: List[FindingCandidate] = []                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         840             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         855             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         871             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         883             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         899             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         915             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         927             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         939             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         949         return findings                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         951     def _extract_functional_findings(                                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         957         findings: List[FindingCandidate] = []                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         960             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         971             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         982             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         992         return findings                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         994     def _extract_safety_findings(                                                                        
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1017     def _extract_caregiver_findings(                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1023         findings: List[FindingCandidate] = []                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1026             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1037             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1047         return findings                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1049     def _extract_respiratory_findings(                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1055         findings: List[FindingCandidate] = []                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1066             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1079             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1090             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1101         return findings                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1103     def _extract_cardiac_findings(                                                                       
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1109         findings: List[FindingCandidate] = []                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1112             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1123             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1133         return findings                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1135     def _extract_cognitive_behavior_findings(                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1141         findings: List[FindingCandidate] = []                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1144             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1156             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1167         return findings                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1169     def _extract_spiritual_findings(                                                                     
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1175         findings: List[FindingCandidate] = []                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1178             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1189             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1200             findings.append(                                                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1210         return findings                                                                                  
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1212     def _load_findings(self, db: Session, reasoning_record_id: UUID) -> List[Dict[str, Any]]:            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1217                 FROM findings                                                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1325     def _link_interpretation_findings(                                                                   
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1335                     INSERT INTO interpretation_findings (                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1377     def _dedupe_findings(findings: List[FindingCandidate]) -> List[FindingCandidate]:                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                        1381         for finding in findings:                                                                         
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                             53     requires_idg_review: bool                                                                            
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                            526         requires_idg_review=(                                                                            
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                            527             policy.requires_idg_review                                                                   
C:\dev\sns emr\backend\app\services\idg_completeness.py                                    7 from app.models.idg_note import IDGNote                                                                  
C:\dev\sns emr\backend\app\services\idg_completeness.py                                    8 from app.models.idg_review import IDGReview                                                              
C:\dev\sns emr\backend\app\services\idg_completeness.py                                   14     idg_review_id,                                                                                       
C:\dev\sns emr\backend\app\services\idg_completeness.py                                   26         db.query(IDGReview)                                                                              
C:\dev\sns emr\backend\app\services\idg_completeness.py                                   28             IDGReview.id == idg_review_id,                                                               
C:\dev\sns emr\backend\app\services\idg_completeness.py                                   29             IDGReview.tenant_id == tenant_id,                                                            
C:\dev\sns emr\backend\app\services\idg_completeness.py                                   35         return ["IDG_REVIEW_NOT_FOUND"]                                                                  
C:\dev\sns emr\backend\app\services\idg_completeness.py                                   49         db.query(IDGNote)                                                                                
C:\dev\sns emr\backend\app\services\idg_completeness.py                                   51             IDGNote.idg_review_id == idg_review_id,                                                      
C:\dev\sns emr\backend\app\services\idg_completeness.py                                   52             IDGNote.tenant_id == tenant_id,                                                              
C:\dev\sns emr\backend\app\services\idg_compliance.py                                      9 from app.models.idg_review import IDGReview                                                              
C:\dev\sns emr\backend\app\services\idg_compliance.py                                     11 from app.models.idg_note import IDGNote                                                                  
C:\dev\sns emr\backend\app\services\idg_compliance.py                                     12 from app.models.idg_meeting import IDGMeeting                                                            
C:\dev\sns emr\backend\app\services\idg_compliance.py                                     47             db.query(IDGReview)                                                                          
C:\dev\sns emr\backend\app\services\idg_compliance.py                                     49                 IDGReview.patient_id == patient.id,                                                      
C:\dev\sns emr\backend\app\services\idg_compliance.py                                     50                 IDGReview.tenant_id == tenant_id,                                                        
C:\dev\sns emr\backend\app\services\idg_compliance.py                                     52             .order_by(IDGReview.review_date.desc())                                                      
C:\dev\sns emr\backend\app\services\idg_compliance.py                                     72                         IDGMDAttestation.idg_review_id == review.id,                                     
C:\dev\sns emr\backend\app\services\idg_compliance.py                                     84                         db.query(IDGNote.discipline)                                                     
C:\dev\sns emr\backend\app\services\idg_compliance.py                                     85                         .filter(IDGNote.idg_review_id == review.id)                                      
C:\dev\sns emr\backend\app\services\idg_compliance.py                                    108                 "last_idg_review_date": review.review_date if review else None,                          
C:\dev\sns emr\backend\app\services\idg_compliance.py                                    121 def get_missed_idg_meetings(                                                                             
C:\dev\sns emr\backend\app\services\idg_compliance.py                                    142             db.query(IDGReview.id)                                                                       
C:\dev\sns emr\backend\app\services\idg_compliance.py                                    144                 IDGReview.idg_meeting_id == meeting.id,                                                  
C:\dev\sns emr\backend\app\services\idg_compliance.py                                    145                 IDGReview.is_finalized == True,                                                          
C:\dev\sns emr\backend\app\services\idg_compliance.py                                    183             db.query(IDGReview.id)                                                                       
C:\dev\sns emr\backend\app\services\idg_compliance.py                                    185                 IDGReview.idg_meeting_id == meeting.id,                                                  
C:\dev\sns emr\backend\app\services\idg_compliance.py                                    186                 IDGReview.is_finalized == True,                                                          
C:\dev\sns emr\backend\app\services\idg_dashboard.py                                      24             Task.task_type == TaskType.IDG_REVIEW,                                                       
C:\dev\sns emr\backend\app\services\idg_dashboard.py                                      47             Task.task_type == TaskType.IDG_REVIEW,                                                       
C:\dev\sns emr\backend\app\services\idg_dashboard_api.py                                  14     get_missed_idg_meetings,                                                                             
C:\dev\sns emr\backend\app\services\idg_dashboard_api.py                                  70     missed_meetings = get_missed_idg_meetings(                                                           
C:\dev\sns emr\backend\app\services\idg_dashboard_api.py                                  86             Task.task_type == TaskType.IDG_REVIEW,                                                       
C:\dev\sns emr\backend\app\services\idg_dashboard_api.py                                  97             Task.task_type == TaskType.IDG_REVIEW,                                                       
C:\dev\sns emr\backend\app\services\idg_dashboard_api.py                                 113         "missed_idg_meetings": missed_count,                                                             
C:\dev\sns emr\backend\app\services\idg_enforcement.py                                    14 from app.models.idg_review import IDGReview                                                              
C:\dev\sns emr\backend\app\services\idg_enforcement.py                                    15 from app.models.idg_note import IDGNote                                                                  
C:\dev\sns emr\backend\app\services\idg_enforcement.py                                    41     idg_review_id: str,                                                                                  
C:\dev\sns emr\backend\app\services\idg_enforcement.py                                    44     Raises HTTPException if the IDGReview cannot be finalized.                                           
C:\dev\sns emr\backend\app\services\idg_enforcement.py                                    51         db.query(IDGReview)                                                                              
C:\dev\sns emr\backend\app\services\idg_enforcement.py                                    52         .filter(IDGReview.id == idg_review_id)                                                           
C:\dev\sns emr\backend\app\services\idg_enforcement.py                                    84         db.query(IDGNote)                                                                                
C:\dev\sns emr\backend\app\services\idg_enforcement.py                                    85         .filter(IDGNote.idg_review_id == review.id)                                                      
C:\dev\sns emr\backend\app\services\idg_enforcement.py                                   116         .filter(IDGMDAttestation.idg_review_id == review.id)                                             
C:\dev\sns emr\backend\app\services\idg_engine.py                                         12 from app.models.idg_review import IDGReview                                                              
C:\dev\sns emr\backend\app\services\idg_engine.py                                         67         db.query(IDGReview)                                                                              
C:\dev\sns emr\backend\app\services\idg_engine.py                                         69             IDGReview.patient_id == patient_id,                                                          
C:\dev\sns emr\backend\app\services\idg_engine.py                                         70             IDGReview.tenant_id == tenant_id,                                                            
C:\dev\sns emr\backend\app\services\idg_engine.py                                         72         .order_by(IDGReview.review_date.desc())                                                          
C:\dev\sns emr\backend\app\services\idg_finalize.py                                        7 from app.models.idg_review import IDGReview                                                              
C:\dev\sns emr\backend\app\services\idg_finalize.py                                       12 def finalize_idg_review(                                                                                 
C:\dev\sns emr\backend\app\services\idg_finalize.py                                       15     idg_review_id,                                                                                       
C:\dev\sns emr\backend\app\services\idg_finalize.py                                       20         db.query(IDGReview)                                                                              
C:\dev\sns emr\backend\app\services\idg_finalize.py                                       21         .filter(IDGReview.id == idg_review_id)                                                           
C:\dev\sns emr\backend\app\services\idg_finalize.py                                       28             "error": "IDG_REVIEW_NOT_FOUND",                                                             
C:\dev\sns emr\backend\app\services\idg_finalize.py                                       47         idg_review_id=idg_review_id,                                                                     
C:\dev\sns emr\backend\app\services\idg_finalize.py                                       59             idg_review=review,                                                                           
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                                8 from app.models.idg_review import IDGReview                                                              
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                                9 from app.models.idg_meeting import IDGMeeting                                                            
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               22     idg_review: IDGReview,                                                                               
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               28             Task.tenant_id == idg_review.tenant_id,                                                      
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               29             Task.patient_id == idg_review.patient_id,                                                    
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               30             Task.idg_meeting_id == idg_review.idg_meeting_id,                                            
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               31             Task.task_type == TaskType.IDG_REVIEW,                                                       
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               43     task.completion_reference_type = "IDG_REVIEW"                                                        
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               44     task.completion_reference_id = idg_review.id                                                         
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               56     idg_review: IDGReview,                                                                               
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               62             IDGMeeting.tenant_id == idg_review.tenant_id,                                                
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               63             IDGMeeting.patient_id == idg_review.patient_id,                                              
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               64             IDGMeeting.meeting_date > idg_review.review_date,                                            
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               83 def finalize_idg_review_and_update_tasks(                                                                
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               86     idg_review: IDGReview,                                                                               
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               92         idg_review=idg_review,                                                                           
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                               98         idg_review=idg_review,                                                                           
C:\dev\sns emr\backend\app\services\idg_meeting_bulk.py                                    5 from app.services.idg_meeting_scheduler import generate_idg_meetings                                     
C:\dev\sns emr\backend\app\services\idg_meeting_bulk.py                                   26         generate_idg_meetings(                                                                           
C:\dev\sns emr\backend\app\services\idg_meeting_scheduler.py                               8 from app.models.idg_meeting import IDGMeeting                                                            
C:\dev\sns emr\backend\app\services\idg_meeting_scheduler.py                              41 def generate_idg_meetings(                                                                               
C:\dev\sns emr\backend\app\services\idg_pdf.py                                            94         last_review = r.get("last_idg_review")                                                           
C:\dev\sns emr\backend\app\services\idg_reminder.py                                       11 from app.models.idg_review import IDGReview                                                              
C:\dev\sns emr\backend\app\services\idg_reminder.py                                       98             IDGReview.patient_id.label("patient_id"),                                                    
C:\dev\sns emr\backend\app\services\idg_reminder.py                                       99             IDGReview.review_date.label("review_date"),                                                  
C:\dev\sns emr\backend\app\services\idg_reminder.py                                      100             IDGReview.is_finalized.label("is_finalized"),                                                
C:\dev\sns emr\backend\app\services\idg_reminder.py                                      101             IDGReview.plan_of_care_version_id.label("plan_of_care_version_id"),                          
C:\dev\sns emr\backend\app\services\idg_reminder.py                                      103         .filter(IDGReview.tenant_id == tenant_id)                                                        
C:\dev\sns emr\backend\app\services\idg_reminder.py                                      105             IDGReview.patient_id.asc(),                                                                  
C:\dev\sns emr\backend\app\services\idg_reminder.py                                      106             IDGReview.review_date.desc().nullslast(),                                                    
C:\dev\sns emr\backend\app\services\idg_reminder.py                                      124             reason = "NO_IDG_REVIEW"                                                                     
C:\dev\sns emr\backend\app\services\idg_reminder.py                                      150         "NO_IDG_REVIEW": 1,                                                                              
C:\dev\sns emr\backend\app\services\idg_review_automation.py                               8 from app.models.idg_meeting import IDGMeeting                                                            
C:\dev\sns emr\backend\app\services\idg_review_automation.py                              31             Task.task_type == TaskType.IDG_REVIEW,                                                       
C:\dev\sns emr\backend\app\services\idg_review_automation.py                              58 def _get_next_idg_meeting(db: Session, tenant_id) -> IDGMeeting:                                         
C:\dev\sns emr\backend\app\services\idg_review_automation.py                              81     meeting = _get_next_idg_meeting(db, patient.tenant_id)                                               
C:\dev\sns emr\backend\app\services\idg_review_automation.py                              90         task_type=TaskType.IDG_REVIEW,                                                                   
C:\dev\sns emr\backend\app\services\idg_review_automation.py                              96         regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,                                                 
C:\dev\sns emr\backend\app\services\idg_review_automation.py                             102         idg_meeting_id=meeting.id,                                                                       
C:\dev\sns emr\backend\app\services\idg_review_automation.py                             140     meeting = _get_next_idg_meeting(db, completed_task.tenant_id)                                        
C:\dev\sns emr\backend\app\services\idg_review_automation.py                             149         task_type=TaskType.IDG_REVIEW,                                                                   
C:\dev\sns emr\backend\app\services\idg_review_automation.py                             155         regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,                                                 
C:\dev\sns emr\backend\app\services\idg_review_automation.py                             161         idg_meeting_id=meeting.id,                                                                       
C:\dev\sns emr\backend\app\services\idg_review_service.py                                  7 def finalize_idg_review(                                                                                 
C:\dev\sns emr\backend\app\services\idg_review_service.py                                 10     idg_review_id,                                                                                       
C:\dev\sns emr\backend\app\services\idg_review_service.py                                 12 ) -> IDGReview:                                                                                          
C:\dev\sns emr\backend\app\services\idg_review_service.py                                 15         db.query(IDGReview)                                                                              
C:\dev\sns emr\backend\app\services\idg_review_service.py                                 16         .filter(IDGReview.id == idg_review_id)                                                           
C:\dev\sns emr\backend\app\services\idg_review_service.py                                 30         validate_idg_ready_to_finalize(db, idg_review_id=idg_review_id)                                  
C:\dev\sns emr\backend\app\services\idg_review_service.py                                 42         complete_current_idg_review_task(db, idg_review=review)                                          
C:\dev\sns emr\backend\app\services\idg_review_service.py                                 67     review: IDGReview,                                                                                   
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                    7 from app.models.idg_review import IDGReview                                                              
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   15 def ensure_initial_idg_review_task(                                                                      
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   32             Task.task_type == TaskType.IDG_REVIEW,                                                       
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   45         task_type=TaskType.IDG_REVIEW,                                                                   
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   56 def complete_current_idg_review_task(                                                                    
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   59     idg_review: IDGReview,                                                                               
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   65             Task.tenant_id == idg_review.tenant_id,                                                      
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   66             Task.patient_id == idg_review.patient_id,                                                    
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   67             Task.benefit_period_id == idg_review.benefit_period_id,                                      
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   68             Task.task_type == TaskType.IDG_REVIEW,                                                       
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   80     task.completion_reference_type = "IDG_REVIEW"                                                        
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   81     task.completion_reference_id = idg_review.id                                                         
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   86 def schedule_next_idg_review_task(                                                                       
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   89     idg_review: IDGReview,                                                                               
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   92     return ensure_initial_idg_review_task(                                                               
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   94         tenant_id=idg_review.tenant_id,                                                                  
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   95         patient_id=idg_review.patient_id,                                                                
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   96         benefit_period_id=idg_review.benefit_period_id,                                                  
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                                   97         anchor_date=idg_review.review_date,                                                              
C:\dev\sns emr\backend\app\services\idg_signature_actions.py                               8 from app.models.idg_review import IDGReview                                                              
C:\dev\sns emr\backend\app\services\idg_signature_actions.py                              16     idg_review_id,                                                                                       
C:\dev\sns emr\backend\app\services\idg_signature_actions.py                              27             IDGAttendee.idg_review_id == idg_review_id,                                                  
C:\dev\sns emr\backend\app\services\idg_signature_actions.py                              54         db.query(IDGReview)                                                                              
C:\dev\sns emr\backend\app\services\idg_signature_actions.py                              55         .filter(IDGReview.id == idg_review_id)                                                           
C:\dev\sns emr\backend\app\services\idg_signature_actions.py                              62             "error": "IDG_REVIEW_NOT_FOUND",                                                             
C:\dev\sns emr\backend\app\services\idg_signature_tasks.py                                12     idg_review,                                                                                          
C:\dev\sns emr\backend\app\services\idg_signature_tasks.py                                33                 Task.patient_id == idg_review.patient_id,                                                
C:\dev\sns emr\backend\app\services\idg_signature_tasks.py                                45             tenant_id=idg_review.tenant_id,                                                              
C:\dev\sns emr\backend\app\services\idg_signature_tasks.py                                46             patient_id=idg_review.patient_id,                                                            
C:\dev\sns emr\backend\app\services\idg_signature_validation.py                           16     idg_review_id,                                                                                       
C:\dev\sns emr\backend\app\services\idg_signature_validation.py                           25         .filter(IDGAttendee.idg_review_id == idg_review_id)                                              
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                     9 from app.models.idg_review import IDGReview                                                              
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                    10 from app.models.idg_meeting import IDGMeeting                                                            
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                    18 def get_next_idg_meeting(                                                                                
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                    58             Task.task_type == TaskType.IDG_REVIEW,                                                       
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                    63             Task.idg_meeting_id == meeting.id,                                                           
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                    75         task_type=TaskType.IDG_REVIEW,                                                                   
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                    81         idg_meeting_id=meeting.id,                                                                       
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                    95     idg_review: IDGReview,                                                                               
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   101             Task.tenant_id == idg_review.tenant_id,                                                      
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   102             Task.patient_id == idg_review.patient_id,                                                    
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   103             Task.idg_meeting_id == idg_review.idg_meeting_id,                                            
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   104             Task.task_type == TaskType.IDG_REVIEW,                                                       
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   118     task.completion_reference_type = "IDG_REVIEW"                                                        
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   119     task.completion_reference_id = idg_review.id                                                         
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   131     idg_review: IDGReview,                                                                               
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   134     next_meeting = get_next_idg_meeting(                                                                 
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   136         tenant_id=idg_review.tenant_id,                                                                  
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   137         patient_id=idg_review.patient_id,                                                                
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   138         after_datetime=idg_review.review_date,                                                           
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   146         tenant_id=idg_review.tenant_id,                                                                  
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   147         patient_id=idg_review.patient_id,                                                                
C:\dev\sns emr\backend\app\services\idg_task_engine.py                                   148         benefit_period_id=idg_review.benefit_period_id,                                                  
C:\dev\sns emr\backend\app\services\idg_task_generator.py                                  7 from app.models.idg_meeting import IDGMeeting                                                            
C:\dev\sns emr\backend\app\services\idg_task_generator.py                                 29         .filter(Task.idg_meeting_id == meeting_id)                                                       
C:\dev\sns emr\backend\app\services\idg_task_generator.py                                 54         task_type=TaskType.IDG_REVIEW,                                                                   
C:\dev\sns emr\backend\app\services\idg_task_generator.py                                 60         regulatory_basis=TaskRegulatoryBasis.IDG_REVIEW,                                                 
C:\dev\sns emr\backend\app\services\idg_task_generator.py                                 66         idg_meeting_id=meeting.id,                                                                       
C:\dev\sns emr\backend\app\services\poc_compiler_rn_mapper.py                           1336                     idg_review_requirements,                                                             
C:\dev\sns emr\backend\app\services\poc_compiler_rn_mapper.py                           1494         "idg_review_requirements": _s(                                                                   
C:\dev\sns emr\backend\app\services\poc_compiler_rn_mapper.py                           1496                 "idg_review_requirements"                                                                
C:\dev\sns emr\backend\app\services\poc_service.py                                       270             idg_review_id=None,                                                                          
C:\dev\sns emr\backend\app\services\poc_service.py                                       337     idg_review_id: Optional[UUID] = None,                                                                
C:\dev\sns emr\backend\app\services\poc_service.py                                       402             idg_review_id=idg_review_id,                                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         47     requires_idg_review: bool                                                                            
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         55     Converts clinical_reasoning_results into diagnosis_recommendations.                                  
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        131                 resolved_requires_idg_review=bool(                                                       
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        132                     getattr(resolved, "requires_idg_review", False)                                      
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        177                 FROM clinical_reasoning_results                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        230                     requires_idg_review,                                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        233                 FROM clinical_reasoning_results                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        303         resolved_requires_idg_review: bool,                                                              
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        352         requires_idg_review = (                                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        353             resolved_requires_idg_review                                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        354             or any(bool(row.get("requires_idg_review")) for row in group_results)                        
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        391                 requires_idg_review=requires_idg_review,                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        404             requires_idg_review=requires_idg_review,                                                     
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        441                     requires_idg_review,                                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        476                     :requires_idg_review,                                                                
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        517                 "requires_idg_review": candidate.requires_idg_review,                                    
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        656         requires_idg_review: bool,                                                                       
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        672         if requires_idg_review:                                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        726             "Generated from clinical_reasoning_results. "                                                
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                           67 def _resolve_regulatory_basis_idg_review() -> TaskRegulatoryBasis:                                       
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                           68     """Return the IDG_REVIEW regulatory basis with safe enum fallback."""                                
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                           69     if hasattr(TaskRegulatoryBasis, "IDG_REVIEW"):                                                       
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                           70         return TaskRegulatoryBasis.IDG_REVIEW                                                            
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                          123 def _ensure_next_idg_review_task(                                                                        
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                          134     Called after completing an IDG_REVIEW task.                                                          
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                          136     idg_type = getattr(TaskType, "IDG_REVIEW", None)                                                     
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                          163         "regulatory_basis": _resolve_regulatory_basis_idg_review(),                                      
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                          294     if getattr(task, "task_type", None) == getattr(TaskType, "IDG_REVIEW", None):                        
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                          295         _ensure_next_idg_review_task(                                                                    
C:\dev\sns emr\backend\app\services\admission\admission_status_engine.py                 219                 "IDG_REVIEW",                                                                            
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                  45         "IDG_REVIEW",                                                                                    




## 8. Task Evidence Linkage Search


Path                                                                        LineNumber Line                                                                                                              
----                                                                        ---------- ----                                                                                                              
C:\dev\sns emr\backend\app\api\med_reconciliation.py                               719             completion_reference_type="MED_RECON_ITEM",                                                           
C:\dev\sns emr\backend\app\api\med_reconciliation.py                               720             completion_reference_id=item.id,                                                                      
C:\dev\sns emr\backend\app\api\patients.py                                        1963     task.completion_reference_type = "NOTE"  # placeholder                                                        
C:\dev\sns emr\backend\app\api\patients.py                                        1964     task.completion_reference_id = str(user_id)                                                                   
C:\dev\sns emr\backend\app\api\router.py                                           159             reference_type="POC",                                                                                 
C:\dev\sns emr\backend\app\api\router.py                                           160             reference_id=poc.get("poc_id"),                                                                       
C:\dev\sns emr\backend\app\api\task_completion.py                                   25 from app.services.task_completion_evidence import complete_task_with_evidence                                     
C:\dev\sns emr\backend\app\api\task_completion.py                                  107 def _map_note_family_to_reference_type(note_family: str) -> CompletionReferenceType:                              
C:\dev\sns emr\backend\app\api\task_completion.py                                  154     if payload.completion_reference_type != CompletionReferenceType.VISIT:                                        
C:\dev\sns emr\backend\app\api\task_completion.py                                  162         visit_id=payload.completion_reference_id,                                                                 
C:\dev\sns emr\backend\app\api\task_completion.py                                  193     complete_task_with_evidence(                                                                                  
C:\dev\sns emr\backend\app\api\task_completion.py                                  196         completion_reference_type=payload.completion_reference_type,                                              
C:\dev\sns emr\backend\app\api\task_completion.py                                  197         completion_reference_id=payload.completion_reference_id,                                                  
C:\dev\sns emr\backend\app\api\task_completion.py                                  204         completion_reference_type=task.completion_reference_type,                                                 
C:\dev\sns emr\backend\app\api\task_completion.py                                  205         completion_reference_id=task.completion_reference_id,                                                     
C:\dev\sns emr\backend\app\api\task_completion.py                                  272     reference_type = _map_note_family_to_reference_type(note_family)                                              
C:\dev\sns emr\backend\app\api\task_completion.py                                  274     complete_task_with_evidence(                                                                                  
C:\dev\sns emr\backend\app\api\task_completion.py                                  277         completion_reference_type=reference_type,                                                                 
C:\dev\sns emr\backend\app\api\task_completion.py                                  278         completion_reference_id=note.id,                                                                          
C:\dev\sns emr\backend\app\api\task_completion.py                                  285         completion_reference_type=task.completion_reference_type,                                                 
C:\dev\sns emr\backend\app\api\task_completion.py                                  286         completion_reference_id=task.completion_reference_id,                                                     
C:\dev\sns emr\backend\app\api\visits.py                                           348     poc_reference_id: Optional[uuid.UUID] = None                                                                  
C:\dev\sns emr\backend\app\api\visits.py                                          1093     task.completion_reference_type = (                                                                            
C:\dev\sns emr\backend\app\api\visits.py                                          1099     task.completion_reference_id = visit.id                                                                       
C:\dev\sns emr\backend\app\api\visits.py                                          1189             Task.completion_reference_id == visit.id,                                                             
C:\dev\sns emr\backend\app\api\visits.py                                          1777             Task.completion_reference_id == visit.id,                                                             
C:\dev\sns emr\backend\app\api\schemas\task_write.py                                16     completion_reference_type: CompletionReferenceType = Field(                                                   
C:\dev\sns emr\backend\app\api\schemas\task_write.py                                23     completion_reference_id: UUID = Field(                                                                        
C:\dev\sns emr\backend\app\compliance\cms\evidence.py                               38     evidence_ref_type: Optional[str] = None,                                                                      
C:\dev\sns emr\backend\app\compliance\cms\evidence.py                               39     evidence_ref_id: Optional[str] = None,                                                                        
C:\dev\sns emr\backend\app\compliance\cms\evidence.py                               54     evidence_type = _norm(evidence_ref_type)                                                                      
C:\dev\sns emr\backend\app\compliance\cms\evidence.py                               55     evidence_id = _norm(evidence_ref_id)                                                                          
C:\dev\sns emr\backend\app\compliance\cms\evidence.py                               80                 "(evidence_ref_type and/or evidence_ref_id)."                                                     
C:\dev\sns emr\backend\app\compliance\runbooks\templates.py                         25   - `tasks.completion_reference_type`, `tasks.completion_reference_id`                                            
C:\dev\sns emr\backend\app\core\task_completion_guard.py                            17     completion_reference_type,                                                                                    
C:\dev\sns emr\backend\app\core\task_completion_guard.py                            18     completion_reference_id,                                                                                      
C:\dev\sns emr\backend\app\core\task_completion_guard.py                            34     if not completion_reference_type:                                                                             
C:\dev\sns emr\backend\app\core\task_completion_guard.py                            37             detail="COMPLETED tasks must have completion_reference_type.",                                        
C:\dev\sns emr\backend\app\core\task_completion_guard.py                            40     if not completion_reference_id:                                                                               
C:\dev\sns emr\backend\app\core\task_completion_guard.py                            43             detail="COMPLETED tasks must have completion_reference_id.",                                          
C:\dev\sns emr\backend\app\domain\tasks\clinical_review_task_engine.py              82         reference_type="CLINICAL_NOTE",                                                                           
C:\dev\sns emr\backend\app\domain\tasks\clinical_review_task_engine.py              83         reference_id=note.id,                                                                                     
C:\dev\sns emr\backend\app\domain\tasks\clinical_review_task_engine.py              86         # completion_reference_type ❌                                                                             
C:\dev\sns emr\backend\app\domain\tasks\clinical_review_task_engine.py              87         # completion_reference_id ❌                                                                               
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py         24 COMPLETION_REFERENCE_TYPE_PREFERRED = "DOCUMENT"                                                                  
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py        127     column = tasks_columns.get("completion_reference_type")                                                       
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py        136     return COMPLETION_REFERENCE_TYPE_PREFERRED in labels                                                          
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py        209     if "reference_id" not in task_columns or "reference_type" not in task_columns:                                
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py        211             "tasks.reference_id/reference_type columns are required for duplicate task cleanup"                   
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py        259     can_write_completion_reference_type = _completion_reference_document_allowed(                                 
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py        366                 WHERE reference_type = 'MED_RECON_ITEM'                                                           
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py        367                   AND reference_id IN :ids                                                                        
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py        411                 if "completion_reference_id" in task_columns:                                                     
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py        412                     task_set_clauses.append("completion_reference_id = :survivor_item_id")                        
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py        416                     "completion_reference_type" in task_columns                                                   
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py        417                     and can_write_completion_reference_type                                                       
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py        420                         "completion_reference_type = :completion_reference_type"                                  
C:\dev\sns emr\backend\app\jobs\backfill_med_recon_duplicate_backlog_sql.py        422                     task_update_params["completion_reference_type"] = COMPLETION_REFERENCE_TYPE_PREFERRED         
C:\dev\sns emr\backend\app\models\chha_visit_outcome.py                             22     poc_reference_id = Column(UUID(as_uuid=True), nullable=True)                                                  
C:\dev\sns emr\backend\app\models\enums.py                                          76     CLINICAL_FOLLOWUP = "CLINICAL_FOLLOWUP"                                                                       
C:\dev\sns emr\backend\app\models\service_coverage_decision.py                      89     evidence_reference_type = Column(                                                                             
C:\dev\sns emr\backend\app\models\service_coverage_decision.py                      95     evidence_reference_id = Column(                                                                               
C:\dev\sns emr\backend\app\models\sfv_requirement.py                                37     trigger_reference_id = Column(UUID(as_uuid=True), nullable=False)                                             
C:\dev\sns emr\backend\app\models\sfv_requirement.py                                86             "trigger_reference_id",                                                                               
C:\dev\sns emr\backend\app\models\task.py                                          138     reference_type = Column(String, nullable=True)                                                                
C:\dev\sns emr\backend\app\models\task.py                                          139     reference_id = Column(UUID(as_uuid=True), nullable=True)                                                      
C:\dev\sns emr\backend\app\models\task.py                                          164     completion_reference_type = Column(                                                                           
C:\dev\sns emr\backend\app\models\task.py                                          169     completion_reference_id = Column(UUID(as_uuid=True), nullable=True)                                           
C:\dev\sns emr\backend\app\scripts\backfill_med_recon_duplicate_backlog.py         288             .filter(Task.reference_type == "MED_RECON_ITEM")                                                      
C:\dev\sns emr\backend\app\scripts\backfill_med_recon_duplicate_backlog.py         289             .filter(Task.reference_id.in_(older_duplicate_ids))                                                   
C:\dev\sns emr\backend\app\scripts\backfill_med_recon_duplicate_backlog.py         302                 completion_reference_type="DOCUMENT",                                                             
C:\dev\sns emr\backend\app\scripts\backfill_med_recon_duplicate_backlog.py         303                 completion_reference_id=survivor.id,                                                              
C:\dev\sns emr\backend\app\services\certification_service.py                        10     complete_task_with_evidence,                                                                                  
C:\dev\sns emr\backend\app\services\certification_service.py                        74     complete_task_with_evidence(                                                                                  
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                         70     outcome.poc_reference_id = getattr(payload, "poc_reference_id", None)                                         
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                        149                 Task.task_type == TaskType.CLINICAL_FOLLOWUP,                                                     
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                        157         if hasattr(Task, "reference_id"):                                                                         
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                        158             query = query.filter(Task.reference_id == visit.id)                                                   
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                        184             if hasattr(existing, "reference_type"):                                                               
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                        185                 existing.reference_type = "VISIT"                                                                 
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                        187             if hasattr(existing, "reference_id"):                                                                 
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                        188                 existing.reference_id = visit.id                                                                  
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                        213                 task_type=TaskType.CLINICAL_FOLLOWUP,                                                             
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                        240             if hasattr(task, "reference_type"):                                                                   
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                        241                 task.reference_type = "VISIT"                                                                     
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                        243             if hasattr(task, "reference_id"):                                                                     
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                        244                 task.reference_id = visit.id                                                                      
C:\dev\sns emr\backend\app\services\clinical_note_validation_engine.py            1378         baseline_ref = assessment.get("rn_baseline_reference_id")                                                 
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                       23 # - For CHANGE_OF_CONDITION reports, create CLINICAL_FOLLOWUP tasks                                               
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                      106               AND task_type = 'CLINICAL_FOLLOWUP'::tasks_task_type_enum                                           
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                      166                 'CLINICAL_FOLLOWUP'::tasks_task_type_enum,                                                        
C:\dev\sns emr\backend\app\services\commlog_to_task_bridge.py                      198         create CLINICAL_FOLLOWUP tasks for assigned clinical users                                                
C:\dev\sns emr\backend\app\services\f2f_service.py                                   8     complete_task_with_evidence,                                                                                  
C:\dev\sns emr\backend\app\services\f2f_service.py                                  63     complete_task_with_evidence(                                                                                  
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         132 def _huv_alert_reason(task_type_name: str, trigger_reference_id) -> str:                                          
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         133     return f"{HUV_ALERT_PREFIX}:{task_type_name}:{trigger_reference_id}"                                          
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         136 def _sfv_alert_reason(trigger_source_type: str, trigger_reference_id) -> str:                                     
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         137     return f"{SFV_ALERT_PREFIX}:{trigger_source_type}:{trigger_reference_id}"                                     
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         213     reference_id,                                                                                                 
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         250         reference_type="VISIT",                                                                                   
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         251         reference_id=reference_id,                                                                                
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         279         reference_id=initial_rn_ica_visit_id,                                                                     
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         291         reference_id=initial_rn_ica_visit_id,                                                                     
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         308     trigger_reference_id,                                                                                         
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         314         .filter(SFVRequirement.trigger_reference_id == trigger_reference_id)                                      
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         325     trigger_reference_id,                                                                                         
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         346         trigger_reference_id=trigger_reference_id,                                                                
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         363         alert_reason=_sfv_alert_reason(trigger_source_type, trigger_reference_id),                                
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         364         reference_id=trigger_reference_id,                                                                        
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         375         trigger_reference_id=trigger_reference_id,                                                                
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         425     if str(completing_visit_id) == str(requirement.trigger_reference_id):                                         
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         440                 completion_reference_type="VISIT",                                                                
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         441                 completion_reference_id=completing_visit_id,                                                      
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         472         trigger_reference_id=initial_rn_ica_visit_id,                                                             
C:\dev\sns emr\backend\app\services\hope_phase_b_engine.py                         515         trigger_reference_id=huv_visit_id,                                                                        
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                         43     task.completion_reference_type = "IDG_REVIEW"                                                                 
C:\dev\sns emr\backend\app\services\idg_lifecycle_engine.py                         44     task.completion_reference_id = idg_review.id                                                                  
C:\dev\sns emr\backend\app\services\idg_review_service.py                          100                 completion_reference_type="IDG",                                                                  
C:\dev\sns emr\backend\app\services\idg_review_service.py                          101                 completion_reference_id=review.id,                                                                
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                             80     task.completion_reference_type = "IDG_REVIEW"                                                                 
C:\dev\sns emr\backend\app\services\idg_review_tasks.py                             81     task.completion_reference_id = idg_review.id                                                                  
C:\dev\sns emr\backend\app\services\idg_task_engine.py                             118     task.completion_reference_type = "IDG_REVIEW"                                                                 
C:\dev\sns emr\backend\app\services\idg_task_engine.py                             119     task.completion_reference_id = idg_review.id                                                                  
C:\dev\sns emr\backend\app\services\med_reconciliation_dedup_service.py            239         .filter(Task.reference_type == "MED_RECON_ITEM")                                                          
C:\dev\sns emr\backend\app\services\med_reconciliation_dedup_service.py            240         .filter(Task.reference_id.in_(older_duplicate_ids))                                                       
C:\dev\sns emr\backend\app\services\med_reconciliation_dedup_service.py            255             completion_reference_type="DOCUMENT",                                                                 
C:\dev\sns emr\backend\app\services\med_reconciliation_dedup_service.py            256             completion_reference_id=survivor.id,                                                                  
C:\dev\sns emr\backend\app\services\poc_task_engine.py                             172             reference_type="POC",                                                                                 
C:\dev\sns emr\backend\app\services\poc_task_engine.py                             173             reference_id=poc.get("poc_id"),                                                                       
C:\dev\sns emr\backend\app\services\poc_task_service.py                            100 def _visit_reference_type() -> CompletionReferenceType | str:                                                     
C:\dev\sns emr\backend\app\services\poc_task_service.py                            250         task.reference_type = "VISIT"                                                                             
C:\dev\sns emr\backend\app\services\poc_task_service.py                            251         task.reference_id = visit.id                                                                              
C:\dev\sns emr\backend\app\services\poc_task_service.py                            276     if hasattr(task, "completion_reference_type"):                                                                
C:\dev\sns emr\backend\app\services\poc_task_service.py                            277         task.completion_reference_type = _visit_reference_type()                                                  
C:\dev\sns emr\backend\app\services\poc_task_service.py                            279     if hasattr(task, "completion_reference_id"):                                                                  
C:\dev\sns emr\backend\app\services\poc_task_service.py                            280         task.completion_reference_id = visit.id                                                                   
C:\dev\sns emr\backend\app\services\poc_update_automation.py                        29 from app.services.task_completion_evidence import complete_task_with_evidence                                     
C:\dev\sns emr\backend\app\services\poc_update_automation.py                        82 def _reference_type_visit() -> CompletionReferenceType | str:                                                     
C:\dev\sns emr\backend\app\services\poc_update_automation.py                       108         .filter(Task.completion_reference_type == _reference_type_visit())                                        
C:\dev\sns emr\backend\app\services\poc_update_automation.py                       109         .filter(Task.completion_reference_id == visit_id)                                                         
C:\dev\sns emr\backend\app\services\poc_update_automation.py                       273             complete_task_with_evidence(                                                                          
C:\dev\sns emr\backend\app\services\poc_update_automation.py                       276                 completion_reference_type=_reference_type_visit(),                                                
C:\dev\sns emr\backend\app\services\poc_update_automation.py                       277                 completion_reference_id=visit.id,                                                                 
C:\dev\sns emr\backend\app\services\poc_update_automation.py                       303         complete_task_with_evidence(                                                                              
C:\dev\sns emr\backend\app\services\poc_update_automation.py                       306             completion_reference_type=_reference_type_visit(),                                                    
C:\dev\sns emr\backend\app\services\poc_update_automation.py                       307             completion_reference_id=visit.id,                                                                     
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                      39 def _reference_type_note():                                                                                       
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                     107         existing_ref_id = getattr(task, "completion_reference_id", None)                                          
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                     114         if hasattr(task, "completion_reference_type"):                                                            
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                     115             task.completion_reference_type = _reference_type_note()                                               
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                     117         if hasattr(task, "completion_reference_id"):                                                              
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                     118             task.completion_reference_id = str(corrected_note_id)                                                 
C:\dev\sns emr\backend\app\services\poc_warning_tasks.py                           154     reference_type=None,                                                                                          
C:\dev\sns emr\backend\app\services\poc_warning_tasks.py                           155     reference_id=None,                                                                                            
C:\dev\sns emr\backend\app\services\poc_warning_tasks.py                           202             completion_reference_type=reference_type,                                                             
C:\dev\sns emr\backend\app\services\poc_warning_tasks.py                           203             completion_reference_id=str(reference_id) if reference_id else None,                                  
C:\dev\sns emr\backend\app\services\recert_f2f_enforcement.py                       46 def complete_task_with_evidence(                                                                                  
C:\dev\sns emr\backend\app\services\recert_f2f_enforcement.py                       71     task.completion_reference_type = ref_type                                                                     
C:\dev\sns emr\backend\app\services\recert_f2f_enforcement.py                       72     task.completion_reference_id = ref_id                                                                         
C:\dev\sns emr\backend\app\services\reconciliation_review_task_service.py           12 RECON_REVIEW_REFERENCE_TYPE = "MED_RECONCILIATION_ITEM"                                                           
C:\dev\sns emr\backend\app\services\reconciliation_review_task_service.py           87         reference_type=RECON_REVIEW_REFERENCE_TYPE,                                                               
C:\dev\sns emr\backend\app\services\reconciliation_review_task_service.py           88         reference_id=item_id,                                                                                     
C:\dev\sns emr\backend\app\services\reconciliation_review_task_service.py          101     completion_reference_type: str,                                                                               
C:\dev\sns emr\backend\app\services\reconciliation_review_task_service.py          102     completion_reference_id,                                                                                      
C:\dev\sns emr\backend\app\services\reconciliation_review_task_service.py          115     task.completion_reference_type = completion_reference_type                                                    
C:\dev\sns emr\backend\app\services\reconciliation_review_task_service.py          116     task.completion_reference_id = completion_reference_id                                                        
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                  21 RECON_REVIEW_REFERENCE_TYPE = "MED_RECON_ITEM"                                                                    
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                  73 def _normalize_completion_reference_type(value: Optional[str]) -> Optional[str]:                                  
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 296         reference_type=RECON_REVIEW_REFERENCE_TYPE,                                                               
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 297         reference_id=effective_item_id,                                                                           
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 308         completion_reference_type=None,                                                                           
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 309         completion_reference_id=None,                                                                             
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 345     completion_reference_type: Optional[str],                                                                     
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 346     completion_reference_id,                                                                                      
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 353     - normalizes completion_reference_type to a DB-allowed value                                                  
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 384     normalized_completion_reference_type = _normalize_completion_reference_type(                                  
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 385         completion_reference_type                                                                                 
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 394         completion_reference_type=normalized_completion_reference_type,                                           
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 395         completion_reference_id=completion_reference_id,                                                          
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 400         "MED_RECON_TASK: completed task_id=%s item_id=%s completion_reference_type=%s completion_reference_id=%s",
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 403         normalized_completion_reference_type,                                                                     
C:\dev\sns emr\backend\app\services\reconciliation_task_service.py                 404         str(completion_reference_id) if completion_reference_id else None,                                        
C:\dev\sns emr\backend\app\services\sfv_completion.py                              156         open_task.completion_reference_type = CompletionReferenceType.VISIT                                       
C:\dev\sns emr\backend\app\services\sfv_completion.py                              157         open_task.completion_reference_id = visit_id                                                              
C:\dev\sns emr\backend\app\services\task_auto_complete_engine.py                    15 from app.services.task_completion_evidence import complete_task_with_evidence                                     
C:\dev\sns emr\backend\app\services\task_auto_complete_engine.py                   109         complete_task_with_evidence(                                                                              
C:\dev\sns emr\backend\app\services\task_auto_complete_engine.py                   112             completion_reference_type=CompletionReferenceType.CLINICAL_NOTE,                                      
C:\dev\sns emr\backend\app\services\task_auto_complete_engine.py                   113             completion_reference_id=note.id,                                                                      
C:\dev\sns emr\backend\app\services\task_completion.py                              14 from app.services.task_completion_evidence import complete_task_with_evidence                                     
C:\dev\sns emr\backend\app\services\task_completion.py                              54         complete_task_with_evidence(                                                                              
C:\dev\sns emr\backend\app\services\task_completion.py                              57             completion_reference_type=CompletionReferenceType.VISIT,                                              
C:\dev\sns emr\backend\app\services\task_completion.py                              58             completion_reference_id=visit.id,                                                                     
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    194 def complete_task_with_evidence(                                                                                  
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    198     completion_reference_type: CompletionReferenceType | None,                                                    
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    199     completion_reference_id: uuid.UUID | None,                                                                    
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    209     - completion_reference_type must be populated                                                                 
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    210     - completion_reference_id must be populated                                                                   
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    225     if completion_reference_type is None or completion_reference_id is None:                                      
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    233     existing_type = getattr(task, "completion_reference_type", None)                                              
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    234     existing_id = getattr(task, "completion_reference_id", None)                                                  
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    240         if existing_type == completion_reference_type and existing_id == completion_reference_id:                 
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    251     if completion_reference_type in (                                                                             
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    258             note_id=completion_reference_id,                                                                      
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    268     if hasattr(task, "completion_reference_type"):                                                                
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    269         task.completion_reference_type = completion_reference_type                                                
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    271     if hasattr(task, "completion_reference_id"):                                                                  
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    272         task.completion_reference_id = completion_reference_id                                                    
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    287         str(getattr(completion_reference_type, "value", completion_reference_type)),                              
C:\dev\sns emr\backend\app\services\task_completion_evidence.py                    288         str(completion_reference_id),                                                                             
C:\dev\sns emr\backend\app\services\task_completion_service.py                      68 def complete_task_with_evidence(                                                                                  
C:\dev\sns emr\backend\app\services\task_completion_service.py                      72     reference_type: CompletionReferenceType,                                                                      
C:\dev\sns emr\backend\app\services\task_completion_service.py                      73     reference_id: UUID,                                                                                           
C:\dev\sns emr\backend\app\services\task_completion_service.py                     101         if not reference_type or not reference_id:                                                                
C:\dev\sns emr\backend\app\services\task_completion_service.py                     108         if reference_type in (                                                                                    
C:\dev\sns emr\backend\app\services\task_completion_service.py                     115                 note_id=reference_id,                                                                             
C:\dev\sns emr\backend\app\services\task_completion_service.py                     121         task.completion_reference_type = reference_type                                                           
C:\dev\sns emr\backend\app\services\task_completion_service.py                     122         task.completion_reference_id = reference_id                                                               
C:\dev\sns emr\backend\app\services\task_completion_service.py                     140             str(reference_type),                                                                                  
C:\dev\sns emr\backend\app\services\task_completion_service.py                     141             str(reference_id),                                                                                    
C:\dev\sns emr\backend\app\services\task_engine.py                                 207     - reference_type / reference_id = source/origin of task                                                       
C:\dev\sns emr\backend\app\services\task_engine.py                                 210     - completion_reference_type                                                                                   
C:\dev\sns emr\backend\app\services\task_engine.py                                 211     - completion_reference_id                                                                                     
C:\dev\sns emr\backend\app\services\task_engine.py                                 214     task_kwargs.pop("completion_reference_type", None)                                                            
C:\dev\sns emr\backend\app\services\task_engine.py                                 215     task_kwargs.pop("completion_reference_id", None)                                                              
C:\dev\sns emr\backend\app\services\task_engine.py                                 222     reference_type: str,                                                                                          
C:\dev\sns emr\backend\app\services\task_engine.py                                 223     reference_id: Any,                                                                                            
C:\dev\sns emr\backend\app\services\task_engine.py                                 228     if hasattr(Task, "reference_type"):                                                                           
C:\dev\sns emr\backend\app\services\task_engine.py                                 229         task_kwargs["reference_type"] = reference_type                                                            
C:\dev\sns emr\backend\app\services\task_engine.py                                 231     if hasattr(Task, "reference_id"):                                                                             
C:\dev\sns emr\backend\app\services\task_engine.py                                 232         task_kwargs["reference_id"] = reference_id                                                                
C:\dev\sns emr\backend\app\services\task_engine.py                                 293                 Task.completion_reference_type == _completion_reference_visit(),                                  
C:\dev\sns emr\backend\app\services\task_engine.py                                 294                 Task.completion_reference_id == visit_id,                                                         
C:\dev\sns emr\backend\app\services\task_engine.py                                 314             "completion_reference_type": _completion_reference_visit(),                                           
C:\dev\sns emr\backend\app\services\task_engine.py                                 315             "completion_reference_id": visit_id,                                                                  
C:\dev\sns emr\backend\app\services\task_engine.py                                 370             reference_type="VISIT",                                                                               
C:\dev\sns emr\backend\app\services\task_engine.py                                 371             reference_id=visit_id,                                                                                
C:\dev\sns emr\backend\app\services\task_engine.py                                 524             .filter(Task.reference_type == "POC")                                                                 
C:\dev\sns emr\backend\app\services\task_engine.py                                 525             .filter(Task.reference_id == poc_id)                                                                  
C:\dev\sns emr\backend\app\services\task_engine.py                                 618         reference_type="CLINICAL_NOTE",                                                                           
C:\dev\sns emr\backend\app\services\task_engine.py                                 619         reference_id=note.id,                                                                                     
C:\dev\sns emr\backend\app\services\task_engine.py                                 674         .filter(Task.reference_type == "POC")                                                                     
C:\dev\sns emr\backend\app\services\task_engine.py                                 675         .filter(Task.reference_id == poc_id)                                                                      
C:\dev\sns emr\backend\app\services\task_service.py                                 21     completion_reference_type: CompletionReferenceType,                                                           
C:\dev\sns emr\backend\app\services\task_service.py                                 22     completion_reference_id: UUID,                                                                                
C:\dev\sns emr\backend\app\services\task_service.py                                 46     task.completion_reference_type = completion_reference_type                                                    
C:\dev\sns emr\backend\app\services\task_service.py                                 47     task.completion_reference_id = completion_reference_id                                                        
C:\dev\sns emr\backend\app\services\task_sla_engine.py                              76     if getattr(task, "completion_reference_type", None) == CompletionReferenceType.VISIT:                         
C:\dev\sns emr\backend\app\services\task_sla_engine.py                              77         visit_id = getattr(task, "completion_reference_id", None)                                                 




## 9. POC Evidence and Review Search


Path                                                                           LineNumber Line                                                                                                               
----                                                                           ---------- ----                                                                                                               
C:\dev\sns emr\backend\app\main.py                                                     58 from app.services.overdue_service import mark_overdue_poc_tasks                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            10 from app.models.chha_poc import CHHAPOC                                                                            
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            14     prefix="/chha-pocs",                                                                                           
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            19 @router.post("/", status_code=status.HTTP_201_CREATED, summary="Create CHHA POC (draft)")                          
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            20 def create_chha_poc(                                                                                               
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            28     poc = CHHAPOC(                                                                                                 
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            36     db.add(poc)                                                                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            37     db.flush()  # ensures poc.id exists                                                                            
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            42         action="CREATE_CHHA_POC",                                                                                  
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            43         entity_type="chha_poc",                                                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            44         entity_id=str(poc.id),                                                                                     
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            49     db.refresh(poc)                                                                                                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            52         "chha_poc_id": str(poc.id),                                                                                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            53         "patient_id": str(poc.patient_id),                                                                         
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            54         "status": poc.status,                                                                                      
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            55         "created_at": poc.created_at,                                                                              
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            59 @router.get("/patient/{patient_id}", summary="List CHHA POCs for a patient")                                       
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            60 def list_chha_pocs_for_patient(                                                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            65     pocs = (                                                                                                       
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            66         db.query(CHHAPOC)                                                                                          
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            67         .filter(CHHAPOC.patient_id == patient_id)                                                                  
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            68         .order_by(CHHAPOC.created_at.desc())                                                                       
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            74             "chha_poc_id": str(poc.id),                                                                            
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            75             "status": poc.status,                                                                                  
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            76             "finalized_at": poc.finalized_at,                                                                      
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            77             "finalized_by": str(poc.finalized_by) if poc.finalized_by else None,                                   
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            78             "effective_start": poc.effective_start,                                                                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            79             "effective_end": poc.effective_end,                                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            80             "frequency": poc.frequency,                                                                            
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            82         for poc in pocs                                                                                            
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            87     "/{chha_poc_id}/finalize",                                                                                     
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            91 def finalize_chha_poc(                                                                                             
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            92     chha_poc_id: uuid.UUID,                                                                                        
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            96     poc = db.query(CHHAPOC).filter(CHHAPOC.id == chha_poc_id).first()                                              
C:\dev\sns emr\backend\app\api\chha_pocs.py                                            97     if not poc:                                                                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           100     if poc.status == "active":                                                                                     
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           103     if poc.status == "superseded":                                                                                 
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           107     active_pocs = (                                                                                                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           108         db.query(CHHAPOC)                                                                                          
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           109         .filter(CHHAPOC.patient_id == poc.patient_id, CHHAPOC.status == "active")                                  
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           112     for old in active_pocs:                                                                                        
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           116     poc.status = "active"                                                                                          
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           117     poc.finalized_at = datetime.utcnow()                                                                           
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           118     poc.finalized_by = user.user_id                                                                                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           119     poc.effective_start = poc.effective_start or datetime.utcnow().date()                                          
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           126         action="FINALIZE_CHHA_POC",                                                                                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           127         entity_type="chha_poc",                                                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           128         entity_id=str(poc.id),                                                                                     
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           133     db.refresh(poc)                                                                                                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           136         "chha_poc_id": str(poc.id),                                                                                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           137         "patient_id": str(poc.patient_id),                                                                         
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           138         "status": poc.status,                                                                                      
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           139         "finalized_at": poc.finalized_at,                                                                          
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           140         "finalized_by": str(poc.finalized_by),                                                                     
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           141         "effective_start": poc.effective_start,                                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           142         "effective_end": poc.effective_end,                                                                        
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           147     "/{chha_poc_id}/supersede",                                                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           151 def supersede_chha_poc(                                                                                            
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           152     chha_poc_id: uuid.UUID,                                                                                        
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           157     poc = db.query(CHHAPOC).filter(CHHAPOC.id == chha_poc_id).first()                                              
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           158     if not poc:                                                                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           161     if poc.status != "active":                                                                                     
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           164     poc.status = "superseded"                                                                                      
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           165     poc.effective_end = datetime.utcnow().date()                                                                   
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           172         action="SUPERSEDE_CHHA_POC",                                                                               
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           173         entity_type="chha_poc",                                                                                    
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           174         entity_id=str(poc.id),                                                                                     
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           179     db.refresh(poc)                                                                                                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           182         "chha_poc_id": str(poc.id),                                                                                
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           183         "patient_id": str(poc.patient_id),                                                                         
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           184         "status": poc.status,                                                                                      
C:\dev\sns emr\backend\app\api\chha_pocs.py                                           185         "effective_end": poc.effective_end,                                                                        
C:\dev\sns emr\backend\app\api\notes.py                                                21 # POC INIT                                                                                                         
C:\dev\sns emr\backend\app\api\notes.py                                                24 def _initialize_plan_of_care_updates(note: ClinicalNote) -> None:                                                  
C:\dev\sns emr\backend\app\api\notes.py                                                25     if note.plan_of_care_updates:                                                                                  
C:\dev\sns emr\backend\app\api\notes.py                                                28     note.plan_of_care_updates = {                                                                                  
C:\dev\sns emr\backend\app\api\notes.py                                                35         "pocs": []                                                                                                 
C:\dev\sns emr\backend\app\api\notes.py                                               132     _initialize_plan_of_care_updates(note)                                                                         
C:\dev\sns emr\backend\app\api\patients.py                                           1738                 TaskType.POC_REVIEW_REQUIRED,                                                                      
C:\dev\sns emr\backend\app\api\patients.py                                           1742                 TaskRegulatoryBasis.POC_UPDATE                                                                     
C:\dev\sns emr\backend\app\api\patients.py                                           1812             TaskType.POC_REVIEW_REQUIRED,                                                                          
C:\dev\sns emr\backend\app\api\patients.py                                           1816             TaskRegulatoryBasis.POC_UPDATE                                                                         
C:\dev\sns emr\backend\app\api\patients.py                                           1933     if task.task_type == TaskType.POC_REVIEW_REQUIRED:                                                             
C:\dev\sns emr\backend\app\api\registry.py                                             22     chha_pocs,                                                                                                     
C:\dev\sns emr\backend\app\api\registry.py                                             39 from app.api.routes.plan_of_care import router as poc_router                                                       
C:\dev\sns emr\backend\app\api\registry.py                                            129         poc_router,                                                                                                
C:\dev\sns emr\backend\app\api\registry.py                                            136         chha_pocs.router,                                                                                          
C:\dev\sns emr\backend\app\api\router.py                                               10 from app.domain.poc.poc_task_rules import POC_TO_TASK_MAP                                                          
C:\dev\sns emr\backend\app\api\router.py                                               71 def _poc_regulatory_basis():                                                                                       
C:\dev\sns emr\backend\app\api\router.py                                               72     return getattr(TaskRegulatoryBasis, "POC_UPDATE", "POC_UPDATE")                                                
C:\dev\sns emr\backend\app\api\router.py                                               79 def _map_poc_severity_to_priority(poc: dict) -> str:                                                               
C:\dev\sns emr\backend\app\api\router.py                                               80     severity = _normalize(poc.get("clinical_summary", {}).get("severity"))                                         
C:\dev\sns emr\backend\app\api\router.py                                              108 def process_pocs_to_tasks(db: Session, *, note: ClinicalNote) -> None:                                             
C:\dev\sns emr\backend\app\api\router.py                                              109     if not note or not note.plan_of_care_updates:                                                                  
C:\dev\sns emr\backend\app\api\router.py                                              112     pocs = note.plan_of_care_updates.get("pocs", [])                                                               
C:\dev\sns emr\backend\app\api\router.py                                              113     if not pocs:                                                                                                   
C:\dev\sns emr\backend\app\api\router.py                                              118     for poc in pocs:                                                                                               
C:\dev\sns emr\backend\app\api\router.py                                              119         problem_code = _normalize(poc.get("problem", {}).get("code"))                                              
C:\dev\sns emr\backend\app\api\router.py                                              123         rule = POC_TO_TASK_MAP.get(problem_code)                                                                   
C:\dev\sns emr\backend\app\api\router.py                                              134             .filter(Task.alert_reason == f"POC_{problem_code}")                                                    
C:\dev\sns emr\backend\app\api\router.py                                              142         priority = _map_poc_severity_to_priority(poc)                                                              
C:\dev\sns emr\backend\app\api\router.py                                              152             clinical_severity=poc.get("clinical_summary", {}).get("severity"),                                     
C:\dev\sns emr\backend\app\api\router.py                                              158             regulatory_basis=_poc_regulatory_basis(),                                                              
C:\dev\sns emr\backend\app\api\router.py                                              159             reference_type="POC",                                                                                  
C:\dev\sns emr\backend\app\api\router.py                                              160             reference_id=poc.get("poc_id"),                                                                        
C:\dev\sns emr\backend\app\api\router.py                                              162             alert_reason=f"POC_{problem_code}",                                                                    
C:\dev\sns emr\backend\app\api\router.py                                              169             "Created POC task task_id=%s note_id=%s",                                                              
C:\dev\sns emr\backend\app\api\survey.py                                               23 SURVEY_OVERDUE_POC_SQL = text("SELECT * FROM survey_overdue_poc_updates")                                          
C:\dev\sns emr\backend\app\api\survey.py                                               25 SURVEY_CRISIS_POC_SQL = text("SELECT * FROM survey_crisis_poc_same_day")                                           
C:\dev\sns emr\backend\app\api\survey.py                                               75 @router.get("/overdue-poc-updates")                                                                                
C:\dev\sns emr\backend\app\api\survey.py                                               76 def overdue_poc_updates(                                                                                           
C:\dev\sns emr\backend\app\api\survey.py                                               83     result = db.execute(SURVEY_OVERDUE_POC_SQL)                                                                    
C:\dev\sns emr\backend\app\api\survey.py                                               99 @router.get("/crisis-poc-same-day")                                                                                
C:\dev\sns emr\backend\app\api\survey.py                                              100 def crisis_poc_same_day(                                                                                           
C:\dev\sns emr\backend\app\api\survey.py                                              107     result = db.execute(SURVEY_CRISIS_POC_SQL)                                                                     
C:\dev\sns emr\backend\app\api\visits.py                                              244         description="Full ROS assessment structure including issues and POC",                                      
C:\dev\sns emr\backend\app\api\visits.py                                              348     poc_reference_id: Optional[uuid.UUID] = None                                                                   
C:\dev\sns emr\backend\app\api\visits.py                                             2241         # ✅ POC TRIGGER DETECTION (KEEP — CRITICAL)                                                                
C:\dev\sns emr\backend\app\api\visits.py                                             2246         poc_update_required = False                                                                                
C:\dev\sns emr\backend\app\api\visits.py                                             2253             poc_update_required = True                                                                             
C:\dev\sns emr\backend\app\api\visits.py                                             2256             poc_update_required = True                                                                             
C:\dev\sns emr\backend\app\api\visits.py                                             2259             poc_update_required = True                                                                             
C:\dev\sns emr\backend\app\api\visits.py                                             2262             "POC_TRIGGER_DETECTION visit_id=%s pain=%s psychosocial=%s spiritual=%s result=%s request_id=%s",      
C:\dev\sns emr\backend\app\api\visits.py                                             2267             poc_update_required,                                                                                   
C:\dev\sns emr\backend\app\api\visits.py                                             2271         if poc_update_required:                                                                                    
C:\dev\sns emr\backend\app\api\visits.py                                             2275                 action="POC_TRIGGER_DETECTED",                                                                     
C:\dev\sns emr\backend\app\api\visits.py                                             2962                 requires_poc_update,                                                                               
C:\dev\sns emr\backend\app\api\visits.py                                             3323             "FINALIZE: BEFORE_POC_POLICY visit_id=%s request_id=%s",                                               
C:\dev\sns emr\backend\app\api\visits.py                                             3328         from app.services.poc_update_automation import on_visit_finalized_apply_poc_policy                         
C:\dev\sns emr\backend\app\api\visits.py                                             3330         on_visit_finalized_apply_poc_policy(                                                                       
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                                18 from app.services.poc_review_gate import (                                                                         
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                                19     POCReviewGateError,                                                                                            
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                                20     enforce_poc_review_gate,                                                                                       
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               114             plan_of_care_updates=payload.get("plan_of_care_updates") or {},                                        
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               141 # REVIEW POC                                                                                                       
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               144 @router.post("/{note_id}/pocs/{poc_id}/review")                                                                    
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               145 def review_generated_poc(                                                                                          
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               147     poc_id: str,                                                                                                   
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               161         updated_poc = review_poc(                                                                                  
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               163             poc_id=poc_id,                                                                                         
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               175             "poc_id": poc_id,                                                                                      
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               176             "status": updated_poc.get("status"),                                                                   
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               177             "reviewed": updated_poc.get("review", {}).get("reviewed"),                                             
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               178             "poc": updated_poc,                                                                                    
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               190             detail=f"Failed to review POC: {exc}"                                                                  
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               219     except POCReviewGateError as exc:                                                                              
C:\dev\sns emr\backend\app\api\clinical_notes\router.py                               225                 "blocking_pocs": exc.blocking_pocs,                                                                
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                  19 from app.services.poc_service import (                                                                             
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                  21     create_new_version as create_new_poc_version_service,                                                          
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                  77 class POCInterventionIn(BaseModel):                                                                                
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                  87 class POCGoalIn(BaseModel):                                                                                        
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                  94     interventions: list[POCInterventionIn] = Field(default_factory=list)                                           
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                  97 class POCProblemIn(BaseModel):                                                                                     
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 109     goals: list[POCGoalIn] = Field(default_factory=list)                                                           
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 112 class POCContentIn(BaseModel):                                                                                     
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 113     problems: list[POCProblemIn] = Field(default_factory=list)                                                     
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 120     change_reason: Optional[str] = "Initial POC creation"                                                          
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 123     poc_content: POCContentIn                                                                                      
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 133     poc_content: POCContentIn                                                                                      
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 157     poc_content: POCContentIn                                                                                      
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 186 def _create_poc_or_raise_http(                                                                                     
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 193     poc_content: dict[str, Any],                                                                                   
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 195     change_reason: Optional[str] = "Initial POC creation",                                                         
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 206             poc_content=poc_content,                                                                               
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 228         if "fk_poc_admission" in raw_message:                                                                      
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 240 def _create_poc_version_or_raise_http(                                                                             
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 255         return create_new_poc_version_service(                                                                     
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 307     - nested poc_content only                                                                                      
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 312     poc = _create_poc_or_raise_http(                                                                               
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 318         poc_content=payload.poc_content.model_dump(exclude_none=True),                                             
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 327         plan_of_care_id=poc.id,                                                                                    
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 352     version = _create_poc_version_or_raise_http(                                                                   
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 357         updated_content=payload.poc_content.model_dump(exclude_none=True),                                         
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 375 # GET CURRENT POC WITH NESTED STRUCTURE                                                                            
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 389     Return the current active PlanOfCare version and its nested poc_content snapshot.                              
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 393     poc = (                                                                                                        
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 402     if not poc:                                                                                                    
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 411         plan_of_care_id=poc.id,                                                                                    
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 428         plan_of_care_id=poc.id,                                                                                    
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 429         patient_id=poc.patient_id,                                                                                 
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 430         admission_id=poc.admission_id,                                                                             
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 431         tenant_id=poc.tenant_id,                                                                                   
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 432         status=poc.status,                                                                                         
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 443             poc_content=POCContentIn.model_validate(snapshot),                                                     
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 469     # ✅ Validate POC exists in tenant                                                                              
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 470     poc = (                                                                                                        
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 479     if not poc:                                                                                                    
C:\dev\sns emr\backend\app\api\routes\plan_of_care.py                                 565         poc_content=POCContentIn.model_validate(snapshot),                                                         
C:\dev\sns emr\backend\app\billing\models\billing_snapshot.py                          61         doc="BILLING / CLAIM / INVOICE / POC_BILLING",                                                             
C:\dev\sns emr\backend\app\compliance\types.py                                         17     "POC_UPDATE",                                                                                                  
C:\dev\sns emr\backend\app\compliance\types.py                                         26     "rule_engine.cms.poc_update",                                                                                  
C:\dev\sns emr\backend\app\compliance\types.py                                         40     code: str                  # e.g., "CMS-418.56-POC-UPDATE"                                                     
C:\dev\sns emr\backend\app\compliance\achc\documentation_timeliness.py                 32     once the TaskType enum is expanded beyond POC_UPDATE.                                                          
C:\dev\sns emr\backend\app\compliance\cms\poc_update.py                                14     code="CMS-418.56-POC-UPDATE",                                                                                  
C:\dev\sns emr\backend\app\compliance\cms\poc_update.py                                20         "Defines timing and evidence requirements for POC updates. "                                               
C:\dev\sns emr\backend\app\compliance\cms\poc_update.py                                49     return rules.get("poc_update_timing", {}) or {}                                                                
C:\dev\sns emr\backend\app\compliance\cms\poc_update.py                               156     CMS Hospice CoP-aligned POC update rule.                                                                       
C:\dev\sns emr\backend\app\compliance\cms\poc_update.py                               190                 task_type="POC_UPDATE",                                                                            
C:\dev\sns emr\backend\app\compliance\cms\poc_update.py                               191                 origin="rule_engine.cms.poc_update",                                                               
C:\dev\sns emr\backend\app\compliance\cms\poc_update.py                               210                 task_type="POC_UPDATE",                                                                            
C:\dev\sns emr\backend\app\compliance\cms\poc_update.py                               211                 origin="rule_engine.cms.poc_update",                                                               
C:\dev\sns emr\backend\app\compliance\cms\__init__.py                                   6 from .poc_update import RULE as POC_UPDATE_RULE                                                                    
C:\dev\sns emr\backend\app\compliance\cms\__init__.py                                   7 from .poc_update import RULES as POC_UPDATE_RULES                                                                  
C:\dev\sns emr\backend\app\compliance\cms\__init__.py                                   8 from .poc_update import evaluate as evaluate_poc_update                                                            
C:\dev\sns emr\backend\app\compliance\cms\__init__.py                                   9 from .poc_update import get_rules as get_poc_update_rules                                                          
C:\dev\sns emr\backend\app\compliance\cms\__init__.py                                  16     "POC_UPDATE_RULE",                                                                                             
C:\dev\sns emr\backend\app\compliance\cms\__init__.py                                  17     "POC_UPDATE_RULES",                                                                                            
C:\dev\sns emr\backend\app\compliance\cms\__init__.py                                  18     "evaluate_poc_update",                                                                                         
C:\dev\sns emr\backend\app\compliance\cms\__init__.py                                  19     "get_poc_update_rules",                                                                                        
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                 24 class PocTriggerPolicy(str, Enum):                                                                                 
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                 26     Canonical POC trigger policies.                                                                                
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                 29     - Routine PERIODIC POC_UPDATE anchoring requires a supervisory RN visit.                                       
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                 32       override the supervisory RN requirement for routine PERIODIC POC_UPDATE anchoring.                           
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                 51 DEFAULT_POC_CYCLE_DAYS = 14                                                                                        
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                 65       to anchor routine PERIODIC POC_UPDATE behavior.                                                              
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                 66     - poc_trigger_policy describes how POC_UPDATE automation should interpret                                      
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                 69       any RN visit can anchor periodic POC behavior.                                                               
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                 74     poc_trigger_policy: PocTriggerPolicy                                                                           
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                 75     poc_due_days: int                                                                                              
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                199     Determine the patient's care model and POC trigger policy.                                                     
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                204       - Same-day RN POC review behavior may be triggered by any finalized RN visit.                                
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                210       - Routine PERIODIC POC_UPDATE anchoring requires supervisory RN visit.                                       
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                223         POC_UPDATE behavior.                                                                                       
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                225         routine POC_UPDATE anchor rule.                                                                            
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                256             poc_trigger_policy=PocTriggerPolicy.SAME_DAY_ANY_RN_CRISIS,                                            
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                257             poc_due_days=0,                                                                                        
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                262                 "CRISIS: any finalized RN visit may trigger same-day POC_UPDATE review. "                          
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                269     # Supervisory RN still required for routine periodic POC anchoring.                                            
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                275             poc_trigger_policy=PocTriggerPolicy.SUPERVISORY_RN_ONLY,                                               
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                276             poc_due_days=DEFAULT_POC_CYCLE_DAYS,                                                                   
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                282                 "but routine PERIODIC POC_UPDATE anchoring still requires a supervisory RN visit."                 
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                294             poc_trigger_policy=PocTriggerPolicy.SUPERVISORY_RN_ONLY,                                               
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                295             poc_due_days=DEFAULT_POC_CYCLE_DAYS,                                                                   
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                301                 "routine PERIODIC POC_UPDATE behavior."                                                            
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                312         poc_trigger_policy=PocTriggerPolicy.SUPERVISORY_RN_ONLY,                                                   
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                313         poc_due_days=DEFAULT_POC_CYCLE_DAYS,                                                                       
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                318             "ROUTINE RN-only: routine PERIODIC POC_UPDATE anchoring requires a supervisory RN visit. "             
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                319             "Non-supervisory RN visits do not anchor the next 14-day periodic POC cycle."                          
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                324 def should_anchor_poc_from_rn_visit(                                                                               
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                330     Determine whether a finalized RN visit may anchor POC_UPDATE behavior.                                         
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                340       - Non-supervisory RN visits must not anchor routine PERIODIC POC_UPDATE behavior.                            
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                356     # Any finalized RN visit may trigger same-day POC review.                                                      
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                359     if decision.poc_trigger_policy == PocTriggerPolicy.SAME_DAY_ANY_RN_CRISIS:                                     
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                366     if decision.poc_trigger_policy == PocTriggerPolicy.SUPERVISORY_RN_ONLY:                                        
C:\dev\sns emr\backend\app\domain\care_model_engine.py                                372     # supervisory requirement for routine periodic POC updates.                                                    
C:\dev\sns emr\backend\app\domain\forms\form_registry.py                              183             attached_forms=["POC_UPDATE"],                                                                         
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                    347         return ["POC_UPDATE"]                                                                                      
C:\dev\sns emr\backend\app\domain\poc\poc_task_rules.py                                 2 # POC → TASK MAPPING RULES                                                                                         
C:\dev\sns emr\backend\app\domain\poc\poc_task_rules.py                                 5 POC_TO_TASK_MAP = {                                                                                                
C:\dev\sns emr\backend\app\domain\tasks\clinical_review_task_engine.py                 79         regulatory_basis="POC_UPDATE",                                                                             
C:\dev\sns emr\backend\app\models\chha_poc.py                                           6 class CHHAPOC(BaseModel):                                                                                          
C:\dev\sns emr\backend\app\models\chha_poc.py                                           7     __tablename__ = "chha_pocs"                                                                                    
C:\dev\sns emr\backend\app\models\chha_poc.py                                          28             raise ValueError("CHHA POC already finalized")                                                         
C:\dev\sns emr\backend\app\models\chha_visit_outcome.py                                21     # Optional linkage to future/actual POC entity if you already have one                                         
C:\dev\sns emr\backend\app\models\chha_visit_outcome.py                                22     poc_reference_id = Column(UUID(as_uuid=True), nullable=True)                                                   
C:\dev\sns emr\backend\app\models\clinical_note.py                                    124     plan_of_care_updates = Column(JSON)                                                                            
C:\dev\sns emr\backend\app\models\eligibility.py                                        8 - Forward-compatible (ADR, IDG, POC linkage)                                                                       
C:\dev\sns emr\backend\app\models\enums.py                                             58     POC_UPDATE = "POC_UPDATE"                                                                                      
C:\dev\sns emr\backend\app\models\enums.py                                             69     POC_NONCOMPLIANT_STRUCTURE = "POC_NONCOMPLIANT_STRUCTURE"                                                      
C:\dev\sns emr\backend\app\models\enums.py                                             70     POC_REVIEW_REQUIRED = "POC_REVIEW_REQUIRED"                                                                    
C:\dev\sns emr\backend\app\models\enums.py                                             71     POC_OUT_OF_SCOPE_CARE = "POC_OUT_OF_SCOPE_CARE"                                                                
C:\dev\sns emr\backend\app\models\enums.py                                             72     POC_STALE_REVIEW = "POC_STALE_REVIEW"                                                                          
C:\dev\sns emr\backend\app\models\enums.py                                             73     POC_PHYSICIAN_REVIEW_REQUIRED = "POC_PHYSICIAN_REVIEW_REQUIRED"                                                
C:\dev\sns emr\backend\app\models\enums.py                                             93     POC_UPDATE = "POC_UPDATE"                                                                                      
C:\dev\sns emr\backend\app\models\enums.py                                            271       medication relatedness, or IDG/POC planning.                                                                 
C:\dev\sns emr\backend\app\models\icd10_hospice_policy.py                              37         POC                                                                                                        
C:\dev\sns emr\backend\app\models\icd10_hospice_policy.py                             119     allow_poc_dx = Column(                                                                                         
C:\dev\sns emr\backend\app\models\idg_review.py                                        35     - Must support future POC linkage enforcement.                                                                 
C:\dev\sns emr\backend\app\models\idg_review.py                                       101     poc_action = Column(                                                                                           
C:\dev\sns emr\backend\app\models\notification.py                                      38     # e.g. TASK_ASSIGNED, ESCALATION, POC_TRIGGER                                                                  
C:\dev\sns emr\backend\app\models\notification.py                                      44     # e.g. TASK, POC, COMMUNICATION_LOG                                                                            
C:\dev\sns emr\backend\app\models\plan_of_care.py                                      31         Index("ix_poc_patient_id", "patient_id"),                                                                  
C:\dev\sns emr\backend\app\models\plan_of_care.py                                      32         Index("ix_poc_tenant_id", "tenant_id"),                                                                    
C:\dev\sns emr\backend\app\models\plan_of_care.py                                      33         Index("ix_poc_admission_id", "admission_id"),                                                              
C:\dev\sns emr\backend\app\models\plan_of_care.py                                      34         Index("ix_poc_status", "status"),                                                                          
C:\dev\sns emr\backend\app\models\plan_of_care.py                                      37         Index("ix_poc_tenant_admission", "tenant_id", "admission_id"),                                             
C:\dev\sns emr\backend\app\models\plan_of_care.py                                      42             name="uq_poc_one_per_admission_per_tenant",                                                            
C:\dev\sns emr\backend\app\models\plan_of_care.py                                      47             name="ck_poc_status",                                                                                  
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                              39             name="uq_poc_versions_per_plan",                                                                       
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                              44             name="ck_poc_version_status",                                                                          
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                              49             name="ck_poc_version_source",                                                                          
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                              52         Index("ix_pocv_plan_id", "plan_of_care_id"),                                                               
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                              53         Index("ix_pocv_tenant_id", "tenant_id"),                                                                   
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                              54         Index("ix_pocv_status", "status"),                                                                         
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                              55         Index("ix_pocv_version_number", "version_number"),                                                         
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                              56         Index("ix_pocv_based_on_version_id", "based_on_version_id"),                                               
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                              57         Index("ix_pocv_idg_review_id", "idg_review_id"),                                                           
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                              61             "ix_pocv_plan_version_desc",                                                                           
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                             180         "POCProblem",                                                                                              
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                             181         back_populates="poc_version",                                                                              
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                             184         order_by="POCProblem.sort_order",                                                                          
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                             188         "PocPhysicianApproval",                                                                                    
C:\dev\sns emr\backend\app\models\plan_of_care_version.py                             189         primaryjoin="PlanOfCareVersion.id == foreign(PocPhysicianApproval.poc_version_id)",                        
C:\dev\sns emr\backend\app\models\poc.py                                                2 # FILE: app/models/poc.py                                                                                          
C:\dev\sns emr\backend\app\models\poc.py                                               37 class POCProblem(Base):                                                                                            
C:\dev\sns emr\backend\app\models\poc.py                                               44     - Anchors goals and interventions under a specific POC version                                                 
C:\dev\sns emr\backend\app\models\poc.py                                               51     __tablename__ = "poc_problems"                                                                                 
C:\dev\sns emr\backend\app\models\poc.py                                               56             "poc_version_id",                                                                                      
C:\dev\sns emr\backend\app\models\poc.py                                               59             name="uq_poc_problems_version_code_dx",                                                                
C:\dev\sns emr\backend\app\models\poc.py                                               63             name="ck_poc_problems_diagnosis_context",                                                              
C:\dev\sns emr\backend\app\models\poc.py                                               67             name="ck_poc_problems_severity",                                                                       
C:\dev\sns emr\backend\app\models\poc.py                                               71             name="ck_poc_problems_status",                                                                         
C:\dev\sns emr\backend\app\models\poc.py                                               75             name="ck_poc_problems_source_kind",                                                                    
C:\dev\sns emr\backend\app\models\poc.py                                               77         Index("ix_poc_problems_tenant_id", "tenant_id"),                                                           
C:\dev\sns emr\backend\app\models\poc.py                                               78         Index("ix_poc_problems_version_id", "poc_version_id"),                                                     
C:\dev\sns emr\backend\app\models\poc.py                                               79         Index("ix_poc_problems_problem_code", "problem_code"),                                                     
C:\dev\sns emr\backend\app\models\poc.py                                               80         Index("ix_poc_problems_source_diagnosis_code", "source_diagnosis_code"),                                   
C:\dev\sns emr\backend\app\models\poc.py                                               81         Index("ix_poc_problems_status", "status"),                                                                 
C:\dev\sns emr\backend\app\models\poc.py                                               82         Index("ix_poc_problems_sort_order", "sort_order"),                                                         
C:\dev\sns emr\backend\app\models\poc.py                                               97     poc_version_id = Column(                                                                                       
C:\dev\sns emr\backend\app\models\poc.py                                              194     poc_version = relationship(                                                                                    
C:\dev\sns emr\backend\app\models\poc.py                                              197         foreign_keys=[poc_version_id],                                                                             
C:\dev\sns emr\backend\app\models\poc.py                                              201         "POCGoal",                                                                                                 
C:\dev\sns emr\backend\app\models\poc.py                                              205         order_by="POCGoal.sort_order",                                                                             
C:\dev\sns emr\backend\app\models\poc.py                                              209 class POCGoal(Base):                                                                                               
C:\dev\sns emr\backend\app\models\poc.py                                              214     - Stores a goal under a single POC problem                                                                     
C:\dev\sns emr\backend\app\models\poc.py                                              219     - Physical DB column name is `poc_problem_id` to match current live DB                                         
C:\dev\sns emr\backend\app\models\poc.py                                              222     __tablename__ = "poc_goals"                                                                                    
C:\dev\sns emr\backend\app\models\poc.py                                              227             name="ck_poc_goals_status",                                                                            
C:\dev\sns emr\backend\app\models\poc.py                                              231             name="ck_poc_goals_source_kind",                                                                       
C:\dev\sns emr\backend\app\models\poc.py                                              233         Index("ix_poc_goals_tenant_id", "tenant_id"),                                                              
C:\dev\sns emr\backend\app\models\poc.py                                              234         Index("ix_poc_goals_poc_problem_id", "poc_problem_id"),                                                    
C:\dev\sns emr\backend\app\models\poc.py                                              235         Index("ix_poc_goals_status", "status"),                                                                    
C:\dev\sns emr\backend\app\models\poc.py                                              236         Index("ix_poc_goals_sort_order", "sort_order"),                                                            
C:\dev\sns emr\backend\app\models\poc.py                                              252     # Physical DB column is poc_problem_id                                                                         
C:\dev\sns emr\backend\app\models\poc.py                                              254         "poc_problem_id",                                                                                          
C:\dev\sns emr\backend\app\models\poc.py                                              256         ForeignKey("poc_problems.id", ondelete="CASCADE"),                                                         
C:\dev\sns emr\backend\app\models\poc.py                                              325         "POCProblem",                                                                                              
C:\dev\sns emr\backend\app\models\poc.py                                              331         "POCIntervention",                                                                                         
C:\dev\sns emr\backend\app\models\poc.py                                              335         order_by="POCIntervention.sort_order",                                                                     
C:\dev\sns emr\backend\app\models\poc.py                                              339 class POCIntervention(Base):                                                                                       
C:\dev\sns emr\backend\app\models\poc.py                                              350     - Physical DB column name is `poc_goal_id` to match current live DB                                            
C:\dev\sns emr\backend\app\models\poc.py                                              353     __tablename__ = "poc_interventions"                                                                            
C:\dev\sns emr\backend\app\models\poc.py                                              358             name="ck_poc_interventions_discipline",                                                                
C:\dev\sns emr\backend\app\models\poc.py                                              362             name="ck_poc_interventions_status",                                                                    
C:\dev\sns emr\backend\app\models\poc.py                                              366             name="ck_poc_interventions_source_kind",                                                               
C:\dev\sns emr\backend\app\models\poc.py                                              368         Index("ix_poc_interventions_tenant_id", "tenant_id"),                                                      
C:\dev\sns emr\backend\app\models\poc.py                                              369         Index("ix_poc_interventions_poc_goal_id", "poc_goal_id"),                                                  
C:\dev\sns emr\backend\app\models\poc.py                                              370         Index("ix_poc_interventions_discipline", "discipline"),                                                    
C:\dev\sns emr\backend\app\models\poc.py                                              371         Index("ix_poc_interventions_status", "status"),                                                            
C:\dev\sns emr\backend\app\models\poc.py                                              372         Index("ix_poc_interventions_sort_order", "sort_order"),                                                    
C:\dev\sns emr\backend\app\models\poc.py                                              388     # Physical DB column is poc_goal_id                                                                            
C:\dev\sns emr\backend\app\models\poc.py                                              390         "poc_goal_id",                                                                                             
C:\dev\sns emr\backend\app\models\poc.py                                              392         ForeignKey("poc_goals.id", ondelete="CASCADE"),                                                            
C:\dev\sns emr\backend\app\models\poc.py                                              466         "POCGoal",                                                                                                 
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                            41 PHYSICIAN_ATTESTATION_VERSION = "POC_PHYSICIAN_ATTESTATION_V1"                                                     
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                            44 class PocPhysicianApproval(Base):                                                                                  
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                            45     __tablename__ = "poc_physician_approvals"                                                                      
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                            51     poc_version_id = Column(UUID(as_uuid=True), nullable=False)                                                    
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                            77         server_default=text("'POC_PHYSICIAN_ATTESTATION_V1'"),                                                     
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           138         "PocPhysicianApprovalDocument",                                                                            
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           145         "PocPhysicianApprovalAuditEvent",                                                                          
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           161             name="ck_poc_physician_approvals_physician_role",                                                      
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           170             name="ck_poc_physician_approvals_approval_method",                                                     
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           182             name="ck_poc_physician_approvals_approval_status",                                                     
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           186             name="ck_poc_physician_approvals_escalation_level",                                                    
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           194             name="ck_poc_physician_approvals_approved_requires_approval_date",                                     
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           202             name="ck_poc_physician_approvals_approved_requires_attestation_text",                                  
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           210             name="ck_poc_physician_approvals_approved_requires_attestation_version",                               
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           224             name="ck_poc_physician_approvals_e_signature_requires_authentication",                                 
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           235             name="ck_poc_physician_approvals_rejection_requires_reason",                                           
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           246             name="ck_poc_physician_approvals_rescission_requires_reason",                                          
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           259             name="ck_poc_physician_approvals_void_requires_reason",                                                
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           267             name="ck_poc_physician_approvals_void_status_requires_is_voided",                                      
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           275             name="ck_poc_physician_approvals_reminder_requires_due_date",                                          
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           283             name="ck_poc_physician_approvals_warning_requires_due_date",                                           
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           291             name="ck_poc_physician_approvals_high_alert_requires_due_date",                                        
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           294             "ix_poc_physician_approvals_tenant_id",                                                                
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           298             "ix_poc_physician_approvals_patient_id",                                                               
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           302             "ix_poc_physician_approvals_poc_version_id",                                                           
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           303             "poc_version_id",                                                                                      
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           306             "ix_poc_physician_approvals_status",                                                                   
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           310             "ix_poc_physician_approvals_due_date",                                                                 
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           314             "ix_poc_physician_approvals_overdue",                                                                  
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           318             "ix_poc_physician_approvals_escalation_level",                                                         
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           322             "ix_poc_physician_approvals_tenant_status",                                                            
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           327             "ix_poc_physician_approvals_tenant_overdue_escalation",                                                
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           333             "ix_poc_physician_approvals_tenant_patient_version",                                                   
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           336             "poc_version_id",                                                                                      
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           339             "ux_poc_physician_approvals_one_active_per_poc_version",                                               
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           341             "poc_version_id",                                                                                      
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           348 class PocPhysicianApprovalDocument(Base):                                                                          
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           349     __tablename__ = "poc_physician_approval_documents"                                                             
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           355     poc_physician_approval_id = Column(                                                                            
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           357         ForeignKey("poc_physician_approvals.id", ondelete="RESTRICT"),                                             
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           362     poc_version_id = Column(UUID(as_uuid=True), nullable=False)                                                    
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           393         ForeignKey("poc_physician_approval_documents.id", ondelete="RESTRICT"),                                    
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           423         "PocPhysicianApproval",                                                                                    
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           428         "PocPhysicianApprovalDocument",                                                                            
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           442             name="ck_poc_physician_approval_documents_file_type",                                                  
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           455             name="ck_poc_physician_approval_documents_uploaded_by_role",                                           
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           463             name="ck_poc_physician_approval_documents_source",                                                     
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           471             name="ck_poc_physician_approval_documents_sha256_length",                                              
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           479             name="ck_poc_physician_approval_documents_indexed_requires_user",                                      
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           487             name="ck_poc_physician_approval_documents_classified_requires_user",                                   
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           498             name="ck_poc_physician_approval_documents_replacement_requires_reason",                                
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           510             name="ck_poc_physician_approval_documents_void_requires_reason",                                       
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           513             "ix_poc_physician_approval_documents_tenant_id",                                                       
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           517             "ix_poc_physician_approval_documents_approval_id",                                                     
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           518             "poc_physician_approval_id",                                                                           
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           521             "ix_poc_physician_approval_documents_patient_id",                                                      
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           525             "ix_poc_physician_approval_documents_poc_version_id",                                                  
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           526             "poc_version_id",                                                                                      
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           529             "ix_poc_physician_approval_documents_uploaded_by",                                                     
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           533             "ix_poc_physician_approval_documents_uploaded_at",                                                     
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           537             "ix_poc_physician_approval_documents_tenant_patient_version",                                          
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           540             "poc_version_id",                                                                                      
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           543             "ix_poc_physician_approval_documents_hash",                                                            
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           547             "ux_poc_physician_approval_documents_one_active_per_approval",                                         
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           549             "poc_physician_approval_id",                                                                           
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           556 class PocPhysicianApprovalAuditEvent(Base):                                                                        
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           557     __tablename__ = "poc_physician_approval_audit_events"                                                          
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           563     poc_physician_approval_id = Column(                                                                            
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           565         ForeignKey("poc_physician_approvals.id", ondelete="RESTRICT"),                                             
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           570     poc_version_id = Column(UUID(as_uuid=True), nullable=False)                                                    
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           588         "PocPhysicianApproval",                                                                                    
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           614             name="ck_poc_physician_approval_audit_events_type",                                                    
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           630             name="ck_poc_physician_approval_audit_events_actor_or_system_event",                                   
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           633             "ix_poc_physician_approval_audit_events_tenant_id",                                                    
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           637             "ix_poc_physician_approval_audit_events_approval_id",                                                  
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           638             "poc_physician_approval_id",                                                                           
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           641             "ix_poc_physician_approval_audit_events_patient_id",                                                   
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           645             "ix_poc_physician_approval_audit_events_poc_version_id",                                               
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           646             "poc_version_id",                                                                                      
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           649             "ix_poc_physician_approval_audit_events_event_type",                                                   
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           653             "ix_poc_physician_approval_audit_events_created_at",                                                   
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           657             "ix_poc_physician_approval_audit_events_tenant_patient_version",                                       
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           660             "poc_version_id",                                                                                      
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                           663             "ix_poc_physician_approval_audit_events_tenant_event_created",                                         
C:\dev\sns emr\backend\app\models\visit.py                                            186     chha_poc_id = Column(UUID(as_uuid=True), nullable=True, index=True)                                            
C:\dev\sns emr\backend\app\models\__init__.py                                         141 # ✅ POC PHYSICIAN APPROVAL TRACKING                                                                                
C:\dev\sns emr\backend\app\models\__init__.py                                         144 from app.models.poc_physician_approval import (                                                                    
C:\dev\sns emr\backend\app\models\__init__.py                                         145     PocPhysicianApproval,                                                                                          
C:\dev\sns emr\backend\app\models\__init__.py                                         146     PocPhysicianApprovalDocument,                                                                                  
C:\dev\sns emr\backend\app\models\__init__.py                                         147     PocPhysicianApprovalAuditEvent,                                                                                
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                    8 class POCSource(BaseModel):                                                                                        
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   18 class POCGeneratorMetadata(BaseModel):                                                                             
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   26 class POCEvidence(BaseModel):                                                                                      
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   31 class POCProblem(BaseModel):                                                                                       
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   36 class POCClinicalSummary(BaseModel):                                                                               
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   40 class POCGoal(BaseModel):                                                                                          
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   46 class POCIntervention(BaseModel):                                                                                  
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   52 class POCDraftItemSource(BaseModel):                                                                               
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   57 class POCDraftItem(BaseModel):                                                                                     
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   58     poc_id: str                                                                                                    
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   61     problem: POCProblem                                                                                            
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   62     clinical_summary: POCClinicalSummary = Field(default_factory=POCClinicalSummary)                               
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   64     goals: list[POCGoal] = Field(default_factory=list)                                                             
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   65     interventions: list[POCIntervention] = Field(default_factory=list)                                             
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   66     evidence: list[POCEvidence] = Field(default_factory=list)                                                      
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   68     source: POCDraftItemSource                                                                                     
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   74 class POCFunctionalEvidence(BaseModel):                                                                            
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   81 class POCDraft(BaseModel):                                                                                         
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   89     source: POCSource                                                                                              
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   92     functional_evidence: POCFunctionalEvidence = Field(                                                            
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   93         default_factory=POCFunctionalEvidence                                                                      
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   96     pocs: list[POCDraftItem] = Field(default_factory=list)                                                         
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                   99     generator: POCGeneratorMetadata                                                                                
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                  102 class POCDraftReviewAction(BaseModel):                                                                             
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                  103     poc_id: str                                                                                                    
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                  106     edited_goals: list[POCGoal] | None = None                                                                      
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                  107     edited_interventions: list[POCIntervention] | None = None                                                      
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                  111 class POCDraftReviewRequest(BaseModel):                                                                            
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                  112     draft: POCDraft                                                                                                
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                  114     actions: list[POCDraftReviewAction] = Field(default_factory=list)                                              
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                  117 class POCDraftReviewResult(BaseModel):                                                                             
C:\dev\sns emr\backend\app\schemas\poc_generation.py                                  120     reviewed_pocs: list[POCDraftItem] = Field(default_factory=list)                                                
C:\dev\sns emr\backend\app\services\admission_authorization_service.py                537     admission_basis = _required_enum_member(TaskRegulatoryBasis, ["IDG_REVIEW", "POC_UPDATE"])                     
C:\dev\sns emr\backend\app\services\care_model_service.py                              34     - Enforce Phase 1 POC policy alignment                                                                         
C:\dev\sns emr\backend\app\services\care_model_service.py                              38         "any RN visit anchors POC"                                                                                 
C:\dev\sns emr\backend\app\services\care_model_service.py                              39     - Actual POC scheduling is enforced in automation layer                                                        
C:\dev\sns emr\backend\app\services\care_model_service.py                              53             "poc_trigger_policy": "UNKNOWN",                                                                       
C:\dev\sns emr\backend\app\services\care_model_service.py                              54             "poc_due_days": 14,                                                                                    
C:\dev\sns emr\backend\app\services\care_model_service.py                              65     poc_trigger_policy = _safe_enum_value(decision.poc_trigger_policy)                                             
C:\dev\sns emr\backend\app\services\care_model_service.py                              74     # Final authority = poc_update_automation layer                                                                
C:\dev\sns emr\backend\app\services\care_model_service.py                              78     if poc_trigger_policy.upper() in ("ANY_RN", "ANY_RN_VISIT"):                                                   
C:\dev\sns emr\backend\app\services\care_model_service.py                              79         poc_trigger_policy = "SUPERVISORY_RN_REQUIRED_FOR_PERIODIC"                                                
C:\dev\sns emr\backend\app\services\care_model_service.py                              84         "poc_trigger_policy": poc_trigger_policy,                                                                  
C:\dev\sns emr\backend\app\services\care_model_service.py                              85         "poc_due_days": int(getattr(decision, "poc_due_days", 14) or 14),                                          
C:\dev\sns emr\backend\app\services\chha_outcome_service.py                            70     outcome.poc_reference_id = getattr(payload, "poc_reference_id", None)                                          
C:\dev\sns emr\backend\app\services\clinical_note_service.py                           25 from app.services.poc_engine import generate_poc_suggestions                                                       
C:\dev\sns emr\backend\app\services\clinical_note_service.py                           26 from app.services.poc_review_gate import enforce_poc_review_gate                                                   
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          150 # INTERNAL — ENSURE POC JSON ALWAYS EXISTS                                                                         
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          153 def _ensure_plan_of_care_updates(note: ClinicalNote) -> None:                                                      
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          154     if isinstance(note.plan_of_care_updates, dict):                                                                
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          157     note.plan_of_care_updates = {                                                                                  
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          164         "pocs": [],                                                                                                
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          166     flag_modified(note, "plan_of_care_updates")                                                                    
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          170     if not isinstance(note.plan_of_care_updates, dict):                                                            
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          171         note.plan_of_care_updates = {"meta": {}, "pocs": []}                                                       
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          173     meta = note.plan_of_care_updates.get("meta", {}) or {}                                                         
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          180     note.plan_of_care_updates["meta"] = meta                                                                       
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          181     note.plan_of_care_updates.setdefault("pocs", [])                                                               
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          183     flag_modified(note, "plan_of_care_updates")                                                                    
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          639     _ensure_plan_of_care_updates(note)                                                                             
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          759     _ensure_plan_of_care_updates(note)                                                                             
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          761     generated_pocs = generate_poc_suggestions(note)                                                                
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          763     if generated_pocs:                                                                                             
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          764         note.plan_of_care_updates["pocs"] = generated_pocs                                                         
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          766         note.plan_of_care_updates.setdefault("pocs", [])                                                           
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          768     flag_modified(note, "plan_of_care_updates")                                                                    
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          771         "POC generated for clinical note note_id=%s patient_id=%s count=%s",                                       
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          774         len(note.plan_of_care_updates.get("pocs", [])),                                                            
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          777     pocs = note.plan_of_care_updates.get("pocs", [])                                                               
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          779     if pocs:                                                                                                       
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          781             "POC task generation skipped. "                                                                        
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          782             "Legacy process_pocs_to_tasks no longer exists and "                                                   
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          783             "POC version architecture is required."                                                                
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          787     flag_modified(note, "plan_of_care_updates")                                                                    
C:\dev\sns emr\backend\app\services\clinical_note_service.py                          998         enforce_poc_review_gate(note)                                                                              
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                      231                         requires_poc_update = TRUE,                                                                
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                      378                     crr.requires_poc_update,                                                                       
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                      674                     requires_poc_update = FALSE,                                                                   
C:\dev\sns emr\backend\app\services\diagnosis_sync_service.py                          23 from app.services.poc_rule_loader import (                                                                         
C:\dev\sns emr\backend\app\services\diagnosis_sync_service.py                          42 #       billing, POC, certification, recertification, NOE,                                                         
C:\dev\sns emr\backend\app\services\diagnosis_sync_service.py                         141         POC                                                                                                        
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                          26     "POC",                                                                                                         
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                         100     if cleaned not in {"REFERRAL", "FACESHEET", "RN_ICA", "CTI", "POC"}:                                           
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                         316     if workflow_context == "POC":                                                                                  
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                         317         if not policy.allow_poc_dx:                                                                                
C:\dev\sns emr\backend\app\services\idg_compliance.py                                  65                 reason = "NO_POC_LINK"                                                                             
C:\dev\sns emr\backend\app\services\idg_remediation.py                                 29     if reason == "NO_POC_LINK":                                                                                    
C:\dev\sns emr\backend\app\services\idg_remediation.py                                 30         return "UPDATE_POC"                                                                                        
C:\dev\sns emr\backend\app\services\idg_reminder.py                                    50     - Missing POC linkage                                                                                          
C:\dev\sns emr\backend\app\services\idg_reminder.py                                   128             reason = "NO_POC_LINK"                                                                                 
C:\dev\sns emr\backend\app\services\idg_reminder.py                                   153         "NO_POC_LINK": 4,                                                                                          
C:\dev\sns emr\backend\app\services\medication_alias_service.py                        13 - Safe for MAR, POC, IDG, and medication reconciliation                                                            
C:\dev\sns emr\backend\app\services\overdue_service.py                                  8 def mark_overdue_poc_tasks(db: Session) -> None:                                                                   
C:\dev\sns emr\backend\app\services\overdue_service.py                                 10     Mark ROUTINE POC_UPDATE tasks as overdue when SLA expires.                                                     
C:\dev\sns emr\backend\app\services\overdue_service.py                                 18             Task.task_type == TaskType.POC_UPDATE,                                                                 
C:\dev\sns emr\backend\app\services\poc_compiler_rn_mapper.py                           2 # FILE: app/services/poc_compiler_rn_mapper.py                                                                     
C:\dev\sns emr\backend\app\services\poc_compiler_rn_mapper.py                           3 # PURPOSE: Convert RN ICA payload -> canonical POC compiler nodes                                                  
C:\dev\sns emr\backend\app\services\poc_compiler_rn_mapper.py                        1349                 FROM poc_outcome_rules                                                                             
C:\dev\sns emr\backend\app\services\poc_compiler_rn_mapper.py                        1385                 FROM poc_intervention_rules                                                                        
C:\dev\sns emr\backend\app\services\poc_compiler_rn_mapper.py                        1619     poc_content = rn_ica_data.get("poc_content")                                                                   
C:\dev\sns emr\backend\app\services\poc_compiler_rn_mapper.py                        1620     if isinstance(poc_content, dict):                                                                              
C:\dev\sns emr\backend\app\services\poc_compiler_rn_mapper.py                        1621         problems = poc_content.get("problems", [])                                                                 
C:\dev\sns emr\backend\app\services\poc_compiler_rn_mapper.py                        1770         raise ValueError("RN ICA payload produced no rule-mapped POC problems")                                    
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                             2 # FILE: app/services/poc_compiler_service.py                                                                       
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                            21 from app.models.poc import POCProblem, POCGoal, POCIntervention                                                    
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                            23 from app.services.poc_compiler_rn_mapper import map_rn_ica_to_problem_nodes                                        
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                            30 class POCCompileResult:                                                                                            
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                            46 def compile_poc_from_ica(                                                                                          
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                            55     change_reason: str = "POC compiled from ICA",                                                                  
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                            58 ) -> POCCompileResult:                                                                                             
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                            62     1. Load root POC + current version                                                                             
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                            73     poc = _load_plan_of_care_or_raise(                                                                             
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                            82         poc=poc,                                                                                                   
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                            98             return POCCompileResult(                                                                               
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           100                 plan_of_care_id=poc.id,                                                                            
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           114         plan_of_care_id=poc.id,                                                                                    
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           134             poc_version_id=new_version.id,                                                                         
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           143         poc.current_version_id = new_version.id                                                                    
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           144         poc.updated_by_user_id = created_by_user_id                                                                
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           148             poc_version_id=new_version.id,                                                                         
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           160     return POCCompileResult(                                                                                       
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           162         plan_of_care_id=poc.id,                                                                                    
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           253     poc_content = msw_ica_data.get("poc_content")                                                                  
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           254     if isinstance(poc_content, dict) and isinstance(poc_content.get("problems"), list):                            
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           255         return poc_content["problems"]                                                                             
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           267     poc_content = sc_ica_data.get("poc_content")                                                                   
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           268     if isinstance(poc_content, dict) and isinstance(poc_content.get("problems"), list):                            
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           269         return poc_content["problems"]                                                                             
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           429     poc = (                                                                                                        
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           437     if not poc:                                                                                                    
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           439     return poc                                                                                                     
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           446     poc: PlanOfCare,                                                                                               
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           448     if poc.current_version_id:                                                                                     
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           452                 PlanOfCareVersion.id == poc.current_version_id,                                                    
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           453                 PlanOfCareVersion.plan_of_care_id == poc.id,                                                       
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           465             PlanOfCareVersion.plan_of_care_id == poc.id,                                                           
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           489     poc_version_id: UUID,                                                                                          
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           498         problem_row = POCProblem(                                                                                  
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           500             poc_version_id=poc_version_id,                                                                         
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           520             goal_row = POCGoal(                                                                                    
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           537                 intervention_row = POCIntervention(                                                                
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           563     poc_version_id: UUID,                                                                                          
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           569         db.query(POCProblem)                                                                                       
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           570         .filter(POCProblem.poc_version_id == poc_version_id)                                                       
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           575         db.query(POCGoal)                                                                                          
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           576         .join(POCProblem, POCGoal.problem_id == POCProblem.id)                                                     
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           577         .filter(POCProblem.poc_version_id == poc_version_id)                                                       
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           582         db.query(POCIntervention)                                                                                  
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           583         .join(POCGoal, POCIntervention.goal_id == POCGoal.id)                                                      
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           584         .join(POCProblem, POCGoal.problem_id == POCProblem.id)                                                     
C:\dev\sns emr\backend\app\services\poc_compiler_service.py                           585         .filter(POCProblem.poc_version_id == poc_version_id)                                                       
C:\dev\sns emr\backend\app\services\poc_engine.py                                       9 POC_ENGINE_VERSION = "4.0.0"                                                                                       
C:\dev\sns emr\backend\app\services\poc_engine.py                                      16 def generate_poc_suggestions(note: ClinicalNote) -> List[Dict[str, Any]]:                                          
C:\dev\sns emr\backend\app\services\poc_engine.py                                      30         ("PAIN", _build_pain_poc, _detect_pain),                                                                   
C:\dev\sns emr\backend\app\services\poc_engine.py                                      31         ("WOUND", _build_wound_poc, _detect_wound),                                                                
C:\dev\sns emr\backend\app\services\poc_engine.py                                      32         ("RESPIRATORY", _build_respiratory_poc, _detect_respiratory),                                              
C:\dev\sns emr\backend\app\services\poc_engine.py                                      33         ("PSYCHOSOCIAL", _build_psychosocial_poc, _detect_psychosocial),                                           
C:\dev\sns emr\backend\app\services\poc_engine.py                                      34         ("SPIRITUAL", _build_spiritual_poc, _detect_spiritual),                                                    
C:\dev\sns emr\backend\app\services\poc_engine.py                                      82 def _build_pain_poc(*, note, content_original, content_normalized):                                                
C:\dev\sns emr\backend\app\services\poc_engine.py                                      83     return _base_poc(note, "PAIN", "Pain Management", "MODERATE", content_original)                                
C:\dev\sns emr\backend\app\services\poc_engine.py                                      86 def _build_wound_poc(*, note, content_original, content_normalized):                                               
C:\dev\sns emr\backend\app\services\poc_engine.py                                      87     return _base_poc(note, "WOUND", "Wound Care", "HIGH", content_original)                                        
C:\dev\sns emr\backend\app\services\poc_engine.py                                      90 def _build_respiratory_poc(*, note, content_original, content_normalized):                                         
C:\dev\sns emr\backend\app\services\poc_engine.py                                      91     return _base_poc(note, "RESP", "Respiratory", "MODERATE", content_original)                                    
C:\dev\sns emr\backend\app\services\poc_engine.py                                      94 def _build_psychosocial_poc(*, note, content_original, content_normalized):                                        
C:\dev\sns emr\backend\app\services\poc_engine.py                                      95     return _base_poc(note, "PSYCH", "Psychosocial", "MODERATE", content_original)                                  
C:\dev\sns emr\backend\app\services\poc_engine.py                                      98 def _build_spiritual_poc(*, note, content_original, content_normalized):                                           
C:\dev\sns emr\backend\app\services\poc_engine.py                                      99     return _base_poc(note, "SPIRIT", "Spiritual Care", "MODERATE", content_original)                               
C:\dev\sns emr\backend\app\services\poc_engine.py                                     106 def _base_poc(note, code, name, severity, evidence):                                                               
C:\dev\sns emr\backend\app\services\poc_engine.py                                     115         "engine_version": POC_ENGINE_VERSION,                                                                      
C:\dev\sns emr\backend\app\services\poc_generation_service.py                           8 from app.services.poc_rule_loader import get_rule_by_icd                                                           
C:\dev\sns emr\backend\app\services\poc_generation_service.py                          17 POC_GENERATION_SERVICE_VERSION = "1.0.0"                                                                           
C:\dev\sns emr\backend\app\services\poc_generation_service.py                          20 def generate_initial_poc_draft(note: ClinicalNote) -> dict[str, Any]:                                              
C:\dev\sns emr\backend\app\services\poc_generation_service.py                          25     - Generates draft POC content only.                                                                            
C:\dev\sns emr\backend\app\services\poc_generation_service.py                          55     pocs: list[dict[str, Any]] = []                                                                                
C:\dev\sns emr\backend\app\services\poc_generation_service.py                          58         pocs.append(_pain_poc(note, observed, assessment, interventions))                                          
C:\dev\sns emr\backend\app\services\poc_generation_service.py                          65         pocs.extend(                                                                                               
C:\dev\sns emr\backend\app\services\poc_generation_service.py                          66             _build_pocs_from_rule(                                                                                 
C:\dev\sns emr\backend\app\services\poc_generation_service.py                          77         pocs.append(                                                                                               
C:\dev\sns emr\backend\app\services\poc_generation_service.py                          78             _respiratory_poc(                                                                                      
C:\dev\sns emr\backend\app\services\poc_generation_service.py                          87         pocs.append(_skin_poc(note, observed, assessment, interventions))                                          
C:\dev\sns emr\backend\app\services\poc_generation_service.py                          90         pocs.append(_nutrition_poc(note, observed, assessment))                                                    
C:\dev\sns emr\backend\app\services\poc_generation_service.py                          93         pocs.append(_fall_safety_poc(note, observed, assessment))                                                  
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         105         pocs.extend(                                                                                               
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         106             _build_pocs_from_rule(                                                                                 
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         117         pocs.append(                                                                                               
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         118             _cognitive_decline_poc(                                                                                
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         134             pocs.extend(                                                                                           
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         135                 _build_pocs_from_rule(                                                                             
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         146         pocs.extend(                                                                                               
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         147             _build_pocs_from_rule(                                                                                 
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         161         pocs.append(                                                                                               
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         162             _cardiac_decline_poc(                                                                                  
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         174         pocs.append(                                                                                               
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         175             _cardiac_decline_poc(                                                                                  
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         183         pocs.append(_functional_decline_poc(note, functional_evidence, observed, assessment))                      
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         186         pocs.append(_caregiver_support_poc(note, observed, assessment))                                            
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         215         "pocs": pocs,                                                                                              
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         218             "service": "poc_generation_service",                                                                   
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         219             "version": POC_GENERATION_SERVICE_VERSION,                                                             
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         227 def _pain_poc(                                                                                                     
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         235     return _poc_item(                                                                                              
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         256 def _respiratory_poc(                                                                                              
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         264     return _poc_item(                                                                                              
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         285 def _skin_poc(                                                                                                     
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         293     return _poc_item(                                                                                              
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         314 def _nutrition_poc(                                                                                                
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         325     return _poc_item(                                                                                              
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         345 def _fall_safety_poc(                                                                                              
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         356     return _poc_item(                                                                                              
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         376 def _cognitive_decline_poc(                                                                                        
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         381     return _poc_item(                                                                                              
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         402 def _cardiac_decline_poc(                                                                                          
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         407     return _poc_item(                                                                                              
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         428 def _functional_decline_poc(                                                                                       
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         434     return _poc_item(                                                                                              
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         455 def _caregiver_support_poc(                                                                                        
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         467     return _poc_item(                                                                                              
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         488 def _poc_item(                                                                                                     
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         499         "poc_id": f"AUTO_{problem_code}",                                                                          
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         523         "engine_version": POC_GENERATION_SERVICE_VERSION,                                                          
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         542 def _build_pocs_from_rule(                                                                                         
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         546     pocs: list[dict[str, Any]] = []                                                                                
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         549         pocs.append(                                                                                               
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         550             _poc_item(                                                                                             
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         572     return pocs                                                                                                    
C:\dev\sns emr\backend\app\services\poc_generation_service.py                         653         tenant_id="POC_GENERATOR",                                                                                 
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                  1 # FILE: poc_review_gate.py                                                                                         
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                 21 class POCReviewGateError(Exception):                                                                               
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                 29 # CORE CHECK — DOES PATIENT HAVE CURRENT POC?                                                                      
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                 51     poc = query.order_by(PlanOfCare.created_at.desc()).first()                                                     
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                 53     if not poc or not poc.current_version_id:                                                                      
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                 59             PlanOfCareVersion.id == poc.current_version_id,                                                        
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                 67             "POC_VERSION_NOT_FOUND tenant_id=%s patient_id=%s poc_id=%s",                                          
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                 70             str(getattr(poc, "id", None)),                                                                         
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                 81 def enforce_poc_gate(                                                                                              
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                 90     Blocks clinical actions if NO current POC exists.                                                              
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                100             "POC_GATE_BLOCK tenant_id=%s patient_id=%s actor=%s",                                                  
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                106         raise POCReviewGateError(                                                                                  
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                108             blocking_reason="POC must exist before proceeding.",                                                   
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                116 def enforce_poc_idg_gate(                                                                                          
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                140     poc = query.order_by(PlanOfCare.created_at.desc()).first()                                                     
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                142     if not poc or not poc.current_version_id:                                                                      
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                143         raise POCReviewGateError(                                                                                  
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                145             blocking_reason="Cannot perform IDG check without POC.",                                               
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                151             PlanOfCareVersion.id == poc.current_version_id,                                                        
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                158         raise POCReviewGateError(                                                                                  
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                159             message="POC version not found.",                                                                      
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                165             "POC_IDG_BLOCK tenant_id=%s patient_id=%s actor=%s",                                                   
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                171         raise POCReviewGateError(                                                                                  
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                172             message="Clinical action blocked: POC not reviewed by IDG.",                                           
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                177 def enforce_poc_review_gate(                                                                                       
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                188     Old code may still import enforce_poc_review_gate().                                                           
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                189     Internally, it now uses enforce_poc_gate().                                                                    
C:\dev\sns emr\backend\app\services\poc_review_gate.py                                191     enforce_poc_gate(                                                                                              
C:\dev\sns emr\backend\app\services\poc_rule_loader.py                                 12     / "poc_generation_rules.json"                                                                                  
C:\dev\sns emr\backend\app\services\poc_rule_loader.py                                 17 def load_poc_rules() -> dict[str, Any]:                                                                            
C:\dev\sns emr\backend\app\services\poc_rule_loader.py                                 23     data = load_poc_rules()                                                                                        
C:\dev\sns emr\backend\app\services\poc_rule_loader.py                                 28     data = load_poc_rules()                                                                                        
C:\dev\sns emr\backend\app\services\poc_rule_loader.py                                 33     data = load_poc_rules()                                                                                        
C:\dev\sns emr\backend\app\services\poc_rule_loader.py                                152 def reload_poc_rules() -> dict[str, Any]:                                                                          
C:\dev\sns emr\backend\app\services\poc_rule_loader.py                                153     load_poc_rules.cache_clear()                                                                                   
C:\dev\sns emr\backend\app\services\poc_rule_loader.py                                154     return load_poc_rules()                                                                                        
C:\dev\sns emr\backend\app\services\poc_service.py                                     15 from app.models.poc import POCProblem, POCGoal, POCIntervention                                                    
C:\dev\sns emr\backend\app\services\poc_service.py                                     16 from app.models.poc_physician_approval import (                                                                    
C:\dev\sns emr\backend\app\services\poc_service.py                                     17     PocPhysicianApproval,                                                                                          
C:\dev\sns emr\backend\app\services\poc_service.py                                     18     PocPhysicianApprovalAuditEvent,                                                                                
C:\dev\sns emr\backend\app\services\poc_service.py                                     23 USE_EXAMPLE_POC_FILE = False                                                                                       
C:\dev\sns emr\backend\app\services\poc_service.py                                     26 EXAMPLE_POC_PATH = os.path.join(BASE_DIR, "app", "examples", "poc_content_example.json")                           
C:\dev\sns emr\backend\app\services\poc_service.py                                     64 def _load_example_poc_content() -> dict[str, Any]:                                                                 
C:\dev\sns emr\backend\app\services\poc_service.py                                     65     with open(EXAMPLE_POC_PATH, "r", encoding="utf-8") as f:                                                       
C:\dev\sns emr\backend\app\services\poc_service.py                                     75         raise ValueError("POC snapshot must be a dictionary")                                                      
C:\dev\sns emr\backend\app\services\poc_service.py                                    124     poc = (                                                                                                        
C:\dev\sns emr\backend\app\services\poc_service.py                                    133     if not poc:                                                                                                    
C:\dev\sns emr\backend\app\services\poc_service.py                                    136     if poc.current_version_id:                                                                                     
C:\dev\sns emr\backend\app\services\poc_service.py                                    140                 PlanOfCareVersion.id == poc.current_version_id,                                                    
C:\dev\sns emr\backend\app\services\poc_service.py                                    149             "POC_CURRENT_VERSION_POINTER_BROKEN tenant_id=%s plan_of_care_id=%s current_version_id=%s",            
C:\dev\sns emr\backend\app\services\poc_service.py                                    152             str(poc.current_version_id),                                                                           
C:\dev\sns emr\backend\app\services\poc_service.py                                    184     poc = query.order_by(PlanOfCare.created_at.desc()).first()                                                     
C:\dev\sns emr\backend\app\services\poc_service.py                                    185     if not poc:                                                                                                    
C:\dev\sns emr\backend\app\services\poc_service.py                                    191         plan_of_care_id=poc.id,                                                                                    
C:\dev\sns emr\backend\app\services\poc_service.py                                    202     poc_content: dict[str, Any],                                                                                   
C:\dev\sns emr\backend\app\services\poc_service.py                                    204     change_reason: Optional[str] = "Initial POC creation",                                                         
C:\dev\sns emr\backend\app\services\poc_service.py                                    212     - POC exists immediately (do not wait for physician approval to create it)                                     
C:\dev\sns emr\backend\app\services\poc_service.py                                    217     if USE_EXAMPLE_POC_FILE:                                                                                       
C:\dev\sns emr\backend\app\services\poc_service.py                                    218         poc_content = _load_example_poc_content()                                                                  
C:\dev\sns emr\backend\app\services\poc_service.py                                    220     _validate_snapshot(poc_content)                                                                                
C:\dev\sns emr\backend\app\services\poc_service.py                                    232         existing_poc = (                                                                                           
C:\dev\sns emr\backend\app\services\poc_service.py                                    241         if existing_poc:                                                                                           
C:\dev\sns emr\backend\app\services\poc_service.py                                    244         poc = PlanOfCare(                                                                                          
C:\dev\sns emr\backend\app\services\poc_service.py                                    256         db.add(poc)                                                                                                
C:\dev\sns emr\backend\app\services\poc_service.py                                    262             plan_of_care_id=poc.id,                                                                                
C:\dev\sns emr\backend\app\services\poc_service.py                                    271             snapshot_json=poc_content,                                                                             
C:\dev\sns emr\backend\app\services\poc_service.py                                    284             snapshot=poc_content,                                                                                  
C:\dev\sns emr\backend\app\services\poc_service.py                                    288         poc.current_version_id = version.id                                                                        
C:\dev\sns emr\backend\app\services\poc_service.py                                    289         poc.updated_at = now                                                                                       
C:\dev\sns emr\backend\app\services\poc_service.py                                    290         poc.updated_by_user_id = created_by_user_id                                                                
C:\dev\sns emr\backend\app\services\poc_service.py                                    297                 poc_version_id=version.id,                                                                         
C:\dev\sns emr\backend\app\services\poc_service.py                                    302         db.refresh(poc)                                                                                            
C:\dev\sns emr\backend\app\services\poc_service.py                                    305             "POC_CREATED tenant_id=%s patient_id=%s admission_id=%s poc_id=%s version_id=%s",                      
C:\dev\sns emr\backend\app\services\poc_service.py                                    309             str(poc.id),                                                                                           
C:\dev\sns emr\backend\app\services\poc_service.py                                    313         return poc                                                                                                 
C:\dev\sns emr\backend\app\services\poc_service.py                                    318             "POC_CREATE_FAILED tenant_id=%s patient_id=%s admission_id=%s",                                        
C:\dev\sns emr\backend\app\services\poc_service.py                                    430                 poc_version_id=new_version.id,                                                                     
C:\dev\sns emr\backend\app\services\poc_service.py                                    438             "POC_VERSION_CREATED tenant_id=%s plan_of_care_id=%s version_id=%s version_number=%s source_kind=%s",  
C:\dev\sns emr\backend\app\services\poc_service.py                                    451             "POC_NEW_VERSION_FAILED tenant_id=%s plan_of_care_id=%s",                                              
C:\dev\sns emr\backend\app\services\poc_service.py                                    495             "POC_VERSION_FINALIZED tenant_id=%s version_id=%s",                                                    
C:\dev\sns emr\backend\app\services\poc_service.py                                    505             "POC_VERSION_FINALIZE_FAILED tenant_id=%s version_id=%s",                                              
C:\dev\sns emr\backend\app\services\poc_service.py                                    560         raise ValueError("POC snapshot must be a dictionary")                                                      
C:\dev\sns emr\backend\app\services\poc_service.py                                    565             "POC_STRUCTURE_NOT_MATERIALIZED tenant_id=%s version_id=%s reason=no_problems_in_snapshot",            
C:\dev\sns emr\backend\app\services\poc_service.py                                    572         raise ValueError("POC snapshot problems must be a list")                                                   
C:\dev\sns emr\backend\app\services\poc_service.py                                    575         "POC_STRUCTURE_PROCESSING tenant_id=%s version_id=%s problem_count=%s",                                    
C:\dev\sns emr\backend\app\services\poc_service.py                                    611         problem = POCProblem(                                                                                      
C:\dev\sns emr\backend\app\services\poc_service.py                                    614             poc_version_id=version.id,                                                                             
C:\dev\sns emr\backend\app\services\poc_service.py                                    638                 "POC_PROBLEM_FLUSH_FAILED tenant_id=%s version_id=%s problem_code=%s",                             
C:\dev\sns emr\backend\app\services\poc_service.py                                    668             goal = POCGoal(                                                                                        
C:\dev\sns emr\backend\app\services\poc_service.py                                    690                     "POC_GOAL_FLUSH_FAILED tenant_id=%s version_id=%s problem_id=%s goal_text=%s",                 
C:\dev\sns emr\backend\app\services\poc_service.py                                    722                 intervention = POCIntervention(                                                                    
C:\dev\sns emr\backend\app\services\poc_service.py                                    745                         "POC_INTERVENTION_FLUSH_FAILED tenant_id=%s version_id=%s goal_id=%s intervention_text=%s",
C:\dev\sns emr\backend\app\services\poc_service.py                                    761     poc_version_id: UUID,                                                                                          
C:\dev\sns emr\backend\app\services\poc_service.py                                    763 ) -> PocPhysicianApproval:                                                                                         
C:\dev\sns emr\backend\app\services\poc_service.py                                    767     This does NOT determine whether the POC version exists.                                                        
C:\dev\sns emr\backend\app\services\poc_service.py                                    770     approval = PocPhysicianApproval(                                                                               
C:\dev\sns emr\backend\app\services\poc_service.py                                    773         poc_version_id=poc_version_id,                                                                             
C:\dev\sns emr\backend\app\services\poc_service.py                                    784     audit = PocPhysicianApprovalAuditEvent(                                                                        
C:\dev\sns emr\backend\app\services\poc_service.py                                    786         poc_physician_approval_id=approval.id,                                                                     
C:\dev\sns emr\backend\app\services\poc_service.py                                    788         poc_version_id=poc_version_id,                                                                             
C:\dev\sns emr\backend\app\services\poc_service.py                                    797         "POC_PHYSICIAN_ATTESTATION_CREATED tenant_id=%s patient_id=%s poc_version_id=%s",                          
C:\dev\sns emr\backend\app\services\poc_service.py                                    800         str(poc_version_id),                                                                                       
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                  7 from app.domain.poc.poc_task_rules import POC_TO_TASK_MAP                                                          
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                 52 def _poc_regulatory_basis():                                                                                       
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                 53     return getattr(TaskRegulatoryBasis, "POC_UPDATE", "POC_UPDATE")                                                
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                 56 def _map_priority(poc):                                                                                            
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                 58         (poc.get("clinical_summary") or {}).get("severity")                                                        
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                 85         .filter(Task.alert_reason == f"POC_{problem_code}")                                                        
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                 98 def process_poc_version_to_tasks(                                                                                  
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                101     poc_version                                                                                                    
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                106     - NO mutation of POC JSON                                                                                      
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                110     if not poc_version:                                                                                            
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                113     poc_data = poc_version.snapshot_json or {}                                                                     
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                114     pocs = poc_data.get("pocs", [])                                                                                
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                116     if not isinstance(pocs, list) or not pocs:                                                                     
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                121     patient_id = poc_version.plan_of_care.patient_id                                                               
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                122     tenant_id = poc_version.plan_of_care.tenant_id                                                                 
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                124     for poc in pocs:                                                                                               
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                125         if not isinstance(poc, dict):                                                                              
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                128         problem = poc.get("problem") or {}                                                                         
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                134         rule = POC_TO_TASK_MAP.get(problem_code)                                                                   
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                155         priority = _map_priority(poc)                                                                              
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                171             regulatory_basis=_poc_regulatory_basis(),                                                              
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                172             reference_type="POC",                                                                                  
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                173             reference_id=poc.get("poc_id"),                                                                        
C:\dev\sns emr\backend\app\services\poc_task_engine.py                                174             alert_reason=f"POC_{problem_code}",                                                                    
C:\dev\sns emr\backend\app\services\poc_task_service.py                                12     should_anchor_poc_from_rn_visit,                                                                               
C:\dev\sns emr\backend\app\services\poc_task_service.py                                46 def _task_type_poc_update() -> TaskType | str:                                                                     
C:\dev\sns emr\backend\app\services\poc_task_service.py                                47     member = getattr(TaskType, "POC_UPDATE", None)                                                                 
C:\dev\sns emr\backend\app\services\poc_task_service.py                                48     return member if member is not None else "POC_UPDATE"                                                          
C:\dev\sns emr\backend\app\services\poc_task_service.py                                51 def _active_poc_statuses() -> list:                                                                                
C:\dev\sns emr\backend\app\services\poc_task_service.py                               105 def _regulatory_basis_poc_update() -> TaskRegulatoryBasis | str:                                                   
C:\dev\sns emr\backend\app\services\poc_task_service.py                               106     member = getattr(TaskRegulatoryBasis, "POC_UPDATE", None)                                                      
C:\dev\sns emr\backend\app\services\poc_task_service.py                               107     return member if member is not None else "POC_UPDATE"                                                          
C:\dev\sns emr\backend\app\services\poc_task_service.py                               191 def get_active_poc_task(db: Session, patient_id, *, tenant_id=None) -> Optional[Task]:                             
C:\dev\sns emr\backend\app\services\poc_task_service.py                               196             Task.task_type == _task_type_poc_update(),                                                             
C:\dev\sns emr\backend\app\services\poc_task_service.py                               197             Task.status.in_(_active_poc_statuses()),                                                               
C:\dev\sns emr\backend\app\services\poc_task_service.py                               208 def create_poc_task(                                                                                               
C:\dev\sns emr\backend\app\services\poc_task_service.py                               218     existing = get_active_poc_task(                                                                                
C:\dev\sns emr\backend\app\services\poc_task_service.py                               232         task_type=_task_type_poc_update(),                                                                         
C:\dev\sns emr\backend\app\services\poc_task_service.py                               239         regulatory_basis=_regulatory_basis_poc_update(),                                                           
C:\dev\sns emr\backend\app\services\poc_task_service.py                               240         alert_reason="POC_UPDATE",                                                                                 
C:\dev\sns emr\backend\app\services\poc_task_service.py                               307 def handle_poc_on_finalized_rn_visit(                                                                              
C:\dev\sns emr\backend\app\services\poc_task_service.py                               326         getattr(decision, "poc_trigger_policy", None),                                                             
C:\dev\sns emr\backend\app\services\poc_task_service.py                               328         getattr(decision, "poc_trigger_policy", None),                                                             
C:\dev\sns emr\backend\app\services\poc_task_service.py                               332         return create_and_complete_same_day_crisis_poc(                                                            
C:\dev\sns emr\backend\app\services\poc_task_service.py                               339     should_anchor = should_anchor_poc_from_rn_visit(                                                               
C:\dev\sns emr\backend\app\services\poc_task_service.py                               347     return create_poc_task(                                                                                        
C:\dev\sns emr\backend\app\services\poc_update_automation.py                           12     should_anchor_poc_from_rn_visit,                                                                               
C:\dev\sns emr\backend\app\services\poc_update_automation.py                           58 def _task_type_poc_update() -> TaskType | str:                                                                     
C:\dev\sns emr\backend\app\services\poc_update_automation.py                           59     return getattr(TaskType, "POC_UPDATE", "POC_UPDATE")                                                           
C:\dev\sns emr\backend\app\services\poc_update_automation.py                           78 def _regulatory_basis_poc_update() -> TaskRegulatoryBasis | str:                                                   
C:\dev\sns emr\backend\app\services\poc_update_automation.py                           79     return getattr(TaskRegulatoryBasis, "POC_UPDATE", "POC_UPDATE")                                                
C:\dev\sns emr\backend\app\services\poc_update_automation.py                           97     Determine whether this visit has already satisfied a POC_UPDATE task.                                          
C:\dev\sns emr\backend\app\services\poc_update_automation.py                          100     POC_UPDATE tasks after the first one is completed.                                                             
C:\dev\sns emr\backend\app\services\poc_update_automation.py                          107         .filter(Task.task_type == _task_type_poc_update())                                                         
C:\dev\sns emr\backend\app\services\poc_update_automation.py                          117 def on_visit_finalized_apply_poc_policy(                                                                           
C:\dev\sns emr\backend\app\services\poc_update_automation.py                          141             "POC update automation skipped because tenant_id is missing "                                          
C:\dev\sns emr\backend\app\services\poc_update_automation.py                          233     should_anchor = should_anchor_poc_from_rn_visit(                                                               
C:\dev\sns emr\backend\app\services\poc_update_automation.py                          267             .filter(Task.task_type == _task_type_poc_update())                                                     
C:\dev\sns emr\backend\app\services\poc_update_automation.py                          289             task_type=_task_type_poc_update(),                                                                     
C:\dev\sns emr\backend\app\services\poc_update_automation.py                          293             regulatory_basis=_regulatory_basis_poc_update(),                                                       
C:\dev\sns emr\backend\app\services\poc_update_automation.py                          294             alert_reason="POC update required due to crisis RN visit",                                             
C:\dev\sns emr\backend\app\services\poc_update_automation.py                          326         .filter(Task.task_type == _task_type_poc_update())                                                         
C:\dev\sns emr\backend\app\services\poc_update_automation.py                          343         task_type=_task_type_poc_update(),                                                                         
C:\dev\sns emr\backend\app\services\poc_update_automation.py                          347         regulatory_basis=_regulatory_basis_poc_update(),                                                           
C:\dev\sns emr\backend\app\services\poc_update_automation.py                          348         alert_reason="POC update required after routine supervisory RN visit",                                     
C:\dev\sns emr\backend\app\services\poc_update_tasks.py                                 1 # app/services/poc_update_tasks.py                                                                                 
C:\dev\sns emr\backend\app\services\poc_update_tasks.py                                11 from app.services.poc_update_automation import on_visit_finalized_apply_poc_policy                                 
C:\dev\sns emr\backend\app\services\poc_update_tasks.py                                17 def handle_poc_update_on_visit_finalize(                                                                           
C:\dev\sns emr\backend\app\services\poc_update_tasks.py                                28     app.services.poc_update_automation.on_visit_finalized_apply_poc_policy                                         
C:\dev\sns emr\backend\app\services\poc_update_tasks.py                                44         logger.error("POC_UPDATE wrapper called with db=None")                                                     
C:\dev\sns emr\backend\app\services\poc_update_tasks.py                                48         logger.warning("POC_UPDATE wrapper called with visit=None")                                                
C:\dev\sns emr\backend\app\services\poc_update_tasks.py                                53             "POC_UPDATE wrapper called with invalid patient visit_id=%s",                                          
C:\dev\sns emr\backend\app\services\poc_update_tasks.py                                62         "POC_UPDATE wrapper invoked visit_id=%s patient_id=%s finalized_by=%s",                                    
C:\dev\sns emr\backend\app\services\poc_update_tasks.py                                72         on_visit_finalized_apply_poc_policy(                                                                       
C:\dev\sns emr\backend\app\services\poc_update_tasks.py                                81             "POC_UPDATE automation completed visit_id=%s patient_id=%s",                                           
C:\dev\sns emr\backend\app\services\poc_update_tasks.py                                89             "POC_UPDATE automation failed visit_id=%s patient_id=%s error=%s",                                     
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                          1 # app/services/poc_warning_autosuggest.py                                                                          
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                         29     Safe resolver for POC_NONCOMPLIANT_STRUCTURE task type.                                                        
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                         31     return "POC_NONCOMPLIANT_STRUCTURE"                                                                            
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                         48 def suggest_close_poc_noncompliant_structure_tasks(                                                                
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                         57     Auto-suggest closure by attaching a corrected POC note as evidence.                                            
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                         70         logger.error("POC autosuggest called with db=None")                                                        
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                         74         logger.warning("POC autosuggest missing patient_id")                                                       
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                         79             "POC autosuggest missing corrected_note_id patient_id=%s",                                             
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                        143                 "type": "POC_NONCOMPLIANT_STRUCTURE",                                                              
C:\dev\sns emr\backend\app\services\poc_warning_autosuggest.py                        155         "POC autosuggest linked %s tasks patient_id=%s note_id=%s",                                                
C:\dev\sns emr\backend\app\services\poc_warning_tasks.py                              199             regulatory_basis="POC_UPDATE",                                                                         
C:\dev\sns emr\backend\app\services\poc_warning_tasks.py                              223                 "type": "POC_WARNING",                                                                             
C:\dev\sns emr\backend\app\services\poc_warning_tasks.py                              234         "POC warning tasks created=%s patient_id=%s task_type=%s",                                                 
C:\dev\sns emr\backend\app\services\poc_warning_tasks.py                              247 def escalate_overdue_poc_warning_tasks(                                                                            
C:\dev\sns emr\backend\app\services\poc_warning_tasks.py                              253     task_type: str = "POC_NONCOMPLIANT_STRUCTURE",                                                                 
C:\dev\sns emr\backend\app\services\poc_warning_tasks.py                              257         logger.error("escalate_overdue_poc_warning_tasks called with db=None")                                     
C:\dev\sns emr\backend\app\services\poc_warning_tasks.py                              313         "Escalated overdue POC warning tasks count=%s",                                                            
C:\dev\sns emr\backend\app\services\task_auto_complete_engine.py                       76     # ✅ ensure POC structure exists                                                                                
C:\dev\sns emr\backend\app\services\task_auto_complete_engine.py                       77     if not isinstance(note.plan_of_care_updates, dict):                                                            
C:\dev\sns emr\backend\app\services\task_auto_complete_engine.py                       80     pocs = note.plan_of_care_updates.get("pocs")                                                                   
C:\dev\sns emr\backend\app\services\task_auto_complete_engine.py                       82     if not isinstance(pocs, list) or not pocs:                                                                     
C:\dev\sns emr\backend\app\services\task_auto_complete_engine.py                       85     # ✅ iterate POC-linked tasks                                                                                   
C:\dev\sns emr\backend\app\services\task_auto_complete_engine.py                       86     for poc in pocs:                                                                                               
C:\dev\sns emr\backend\app\services\task_auto_complete_engine.py                       87         if not isinstance(poc, dict):                                                                              
C:\dev\sns emr\backend\app\services\task_auto_complete_engine.py                       90         task_id = poc.get("task_id")                                                                               
C:\dev\sns emr\backend\app\services\task_completion.py                                 40         TaskType.POC_UPDATE,                                                                                       
C:\dev\sns emr\backend\app\services\task_completion_service.py                         22 from app.services.poc_review_gate import enforce_poc_gate                                                          
C:\dev\sns emr\backend\app\services\task_completion_service.py                         88         # ✅ STEP 1 — POC GATE (CRITICAL)                                                                           
C:\dev\sns emr\backend\app\services\task_completion_service.py                         89         enforce_poc_gate(                                                                                          
C:\dev\sns emr\backend\app\services\task_engine.py                                    235 def _poc_alert_reason(problem_code: str) -> str:                                                                   
C:\dev\sns emr\backend\app\services\task_engine.py                                    236     return f"POC_{problem_code}"                                                                                   
C:\dev\sns emr\backend\app\services\task_engine.py                                    256     - CRISIS: finalized RN visit creates and completes same-day POC_UPDATE                                         
C:\dev\sns emr\backend\app\services\task_engine.py                                    257     - ROUTINE: supervisory RN visit creates next periodic POC_UPDATE due_date = visit_date + 14 days               
C:\dev\sns emr\backend\app\services\task_engine.py                                    260     task_type_poc = _task_type_required("POC_UPDATE")                                                              
C:\dev\sns emr\backend\app\services\task_engine.py                                    261     reg_basis_poc = _reg_basis_optional("POC_UPDATE")                                                              
C:\dev\sns emr\backend\app\services\task_engine.py                                    284     # CRISIS: create + complete same-day POC_UPDATE                                                                
C:\dev\sns emr\backend\app\services\task_engine.py                                    292                 Task.task_type == task_type_poc,                                                                   
C:\dev\sns emr\backend\app\services\task_engine.py                                    307             "task_type": task_type_poc,                                                                            
C:\dev\sns emr\backend\app\services\task_engine.py                                    320         if reg_basis_poc is not None:                                                                              
C:\dev\sns emr\backend\app\services\task_engine.py                                    321             task_kwargs["regulatory_basis"] = reg_basis_poc                                                        
C:\dev\sns emr\backend\app\services\task_engine.py                                    342                 Task.task_type == task_type_poc,                                                                   
C:\dev\sns emr\backend\app\services\task_engine.py                                    357             "task_type": task_type_poc,                                                                            
C:\dev\sns emr\backend\app\services\task_engine.py                                    376         if reg_basis_poc is not None:                                                                              
C:\dev\sns emr\backend\app\services\task_engine.py                                    377             task_kwargs["regulatory_basis"] = reg_basis_poc                                                        
C:\dev\sns emr\backend\app\services\task_engine.py                                    405     POC-generated note tasks are handled by the canonical                                                          
C:\dev\sns emr\backend\app\services\task_engine.py                                    406     POC workflow and must not be duplicated here.                                                                  
C:\dev\sns emr\backend\app\services\task_engine.py                                    472 # POC -> TASK BRIDGE (LEGACY / NO-OP)                                                                              
C:\dev\sns emr\backend\app\services\task_engine.py                                    475 def process_poc_tasks_for_note(                                                                                    
C:\dev\sns emr\backend\app\services\task_engine.py                                    484     Canonical POC follow-up task creation is handled by:                                                           
C:\dev\sns emr\backend\app\services\task_engine.py                                    485         app.services.poc_task_engine.process_pocs_to_tasks                                                         
C:\dev\sns emr\backend\app\services\task_engine.py                                    487     This function now only backfills/link-marks already generated POCs when a                                      
C:\dev\sns emr\backend\app\services\task_engine.py                                    490     if not isinstance(note.plan_of_care_updates, dict):                                                            
C:\dev\sns emr\backend\app\services\task_engine.py                                    493     pocs = note.plan_of_care_updates.get("pocs")                                                                   
C:\dev\sns emr\backend\app\services\task_engine.py                                    494     if not isinstance(pocs, list) or len(pocs) == 0:                                                               
C:\dev\sns emr\backend\app\services\task_engine.py                                    499     for poc in pocs:                                                                                               
C:\dev\sns emr\backend\app\services\task_engine.py                                    500         if not isinstance(poc, dict):                                                                              
C:\dev\sns emr\backend\app\services\task_engine.py                                    503         if poc.get("task_generated"):                                                                              
C:\dev\sns emr\backend\app\services\task_engine.py                                    506         problem = poc.get("problem")                                                                               
C:\dev\sns emr\backend\app\services\task_engine.py                                    514         poc_id = poc.get("poc_id")                                                                                 
C:\dev\sns emr\backend\app\services\task_engine.py                                    524             .filter(Task.reference_type == "POC")                                                                  
C:\dev\sns emr\backend\app\services\task_engine.py                                    525             .filter(Task.reference_id == poc_id)                                                                   
C:\dev\sns emr\backend\app\services\task_engine.py                                    538                 .filter(Task.alert_reason == _poc_alert_reason(code))                                              
C:\dev\sns emr\backend\app\services\task_engine.py                                    545         poc["task_generated"] = True                                                                               
C:\dev\sns emr\backend\app\services\task_engine.py                                    546         poc["task_id"] = str(existing.id)                                                                          
C:\dev\sns emr\backend\app\services\task_engine.py                                    548         if "task_history" not in poc or not isinstance(poc["task_history"], list):                                 
C:\dev\sns emr\backend\app\services\task_engine.py                                    549             poc["task_history"] = []                                                                               
C:\dev\sns emr\backend\app\services\task_engine.py                                    551         poc["task_history"].append(                                                                                
C:\dev\sns emr\backend\app\services\task_engine.py                                    562         flag_modified(note, "plan_of_care_updates")                                                                
C:\dev\sns emr\backend\app\services\task_engine.py                                    644 # LEGACY POC HELPERS (KEPT FOR COMPATIBILITY / UNUSED)                                                             
C:\dev\sns emr\backend\app\services\task_engine.py                                    647 def _create_poc_followup_task(                                                                                     
C:\dev\sns emr\backend\app\services\task_engine.py                                    652     poc: dict,                                                                                                     
C:\dev\sns emr\backend\app\services\task_engine.py                                    658     Canonical POC follow-up task creation was moved to:                                                            
C:\dev\sns emr\backend\app\services\task_engine.py                                    659         app.services.poc_task_engine.process_pocs_to_tasks                                                         
C:\dev\sns emr\backend\app\services\task_engine.py                                    664     poc_id = poc.get("poc_id")                                                                                     
C:\dev\sns emr\backend\app\services\task_engine.py                                    674         .filter(Task.reference_type == "POC")                                                                      
C:\dev\sns emr\backend\app\services\task_engine.py                                    675         .filter(Task.reference_id == poc_id)                                                                       
C:\dev\sns emr\backend\app\services\task_engine.py                                    711 def _find_existing_poc_task(                                                                                       
C:\dev\sns emr\backend\app\services\task_engine.py                                    733 # POC TASK MAPPING                                                                                                 
C:\dev\sns emr\backend\app\services\task_engine.py                                    736 def _discipline_for_poc(problem_code: str):                                                                        
C:\dev\sns emr\backend\app\services\task_engine.py                                    746 def _poc_task_description(problem_code: str) -> str:                                                               
C:\dev\sns emr\backend\app\services\task_engine.py                                    749             "Review generated Pain POC, pain assessment, medication effectiveness, "                               
C:\dev\sns emr\backend\app\services\task_engine.py                                    755             "Review generated Wound / Skin Integrity POC, wound status, drainage, "                                
C:\dev\sns emr\backend\app\services\task_engine.py                                    761             "Review generated Respiratory POC, dyspnea status, oxygen use, "                                       
C:\dev\sns emr\backend\app\services\task_engine.py                                    767             "Review generated Psychosocial Support POC, caregiver stress, coping status, "                         
C:\dev\sns emr\backend\app\services\task_engine.py                                    773             "Review generated Spiritual Care POC, chaplain request, prayer/spiritual "                             
C:\dev\sns emr\backend\app\services\task_notification_engine.py                        49             Task.task_type == TaskType.POC_UPDATE,  # ✅ focused on POC initially                                   
C:\dev\sns emr\backend\app\services\task_notification_engine.py                        64             _notify(task, "POC DUE IN 3 DAYS")                                                                     
C:\dev\sns emr\backend\app\services\task_notification_engine.py                        70             _notify(task, "POC DUE TOMORROW")                                                                      
C:\dev\sns emr\backend\app\services\task_notification_engine.py                        76             _notify(task, "POC DUE TODAY")                                                                         
C:\dev\sns emr\backend\app\services\admission\admission_status_engine.py              179                 "POC_WORKFLOW",                                                                                    
C:\dev\sns emr\backend\app\services\admission\admission_status_engine.py              212                 "POC_WORKFLOW",                                                                                    
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py                9 - Prevent RN ICA / POC / CTI / NOE tasks from appearing before SOC.                                                
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py               38         "POC_WORKFLOW",                                                                                            
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py              299             "POC_WORKFLOW",                                                                                        
C:\dev\sns emr\backend\app\services\admission\task_visibility_service.py              330                     "CHHA_POC",                                                                                    
C:\dev\sns emr\backend\app\services\eligibility\eligibility_summary_service.py         21     - create POCs                                                                                                  
C:\dev\sns emr\backend\app\utils\drug_alias.py                                         24     - Safe for MAR, POC, IDG, and reconciliation workflows                                                         




## 10. RN Review and MD Review Search


Path                                                                              LineNumber Line                                                                                    
----                                                                              ---------- ----                                                                                    
C:\dev\sns emr\backend\app\api\soc_orders.py                                             110                 "requires_md_review": guardrail_result["requires_md_review"],           
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                        23         "requires_md_review": False,                                                    
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                        28         "requires_md_review": False,                                                    
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                        34         "requires_md_review": False,                                                    
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                        39         "requires_md_review": True,                                                     
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                        44         "requires_md_review": True,                                                     
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                        49         "requires_md_review": False,                                                    
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                        54         "requires_md_review": False,                                                    
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                       147         "requires_md_review": config.get("requires_md_review", False),                  
C:\dev\sns emr\backend\app\domain\forms\form_resolution_service.py                       381             "requires_md_review": bool,                                                 
C:\dev\sns emr\backend\app\models\icd10_hospice_policy.py                                139     requires_md_review = Column(                                                        
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                              102     rejection_reason = Column(Text, nullable=True)                                      
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                              103     rejected_by_user_id = Column(UUID(as_uuid=True), nullable=True)                     
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                              104     rejected_at = Column(DateTime(timezone=True), nullable=True)                        
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                              231                 rejection_reason IS NOT NULL                                            
C:\dev\sns emr\backend\app\models\poc_physician_approval.py                              232                 AND rejected_at IS NOT NULL                                             
C:\dev\sns emr\backend\app\services\admission_guardrails_service.py                       22     requires_md_review: bool                                                            
C:\dev\sns emr\backend\app\services\admission_guardrails_service.py                      116         requires_md_review = False                                                      
C:\dev\sns emr\backend\app\services\admission_guardrails_service.py                      162             requires_md_review = True                                                   
C:\dev\sns emr\backend\app\services\admission_guardrails_service.py                      171             "requires_md_review": requires_md_review,                                   
C:\dev\sns emr\backend\app\services\clinical_note_service.py                             323     if requirements.get("requires_md_review"):                                          
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         299                 "requires_rn_review": False,                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         350                 "requires_rn_review": False,                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         357                 "requires_rn_review": False,                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         363             "requires_rn_review": True,                                                 
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         518             requires_rn_review = bool(pain_diagnosis["requires_rn_review"])             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         542                         requires_rn_review,                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         543                         requires_md_review,                                             
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         545                         accepted_by,                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         546                         accepted_at,                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         547                         rejected_by,                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         548                         rejected_at,                                                    
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         549                         rejection_reason,                                               
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         571                         :requires_rn_review,                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         572                         :requires_md_review,                                            
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         608                         "requires_rn_review": requires_rn_review,                       
C:\dev\sns emr\backend\app\services\clinical_reasoning_engine.py                         609                         "requires_md_review": bool(record["requires_physician_review"]),
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                             52     requires_md_review: bool                                                            
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                            520         requires_md_review=(                                                            
C:\dev\sns emr\backend\app\services\icd10_resolver_service.py                            521             policy.requires_md_review                                                   
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         45     requires_rn_review: bool                                                            
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py         46     requires_md_review: bool                                                            
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        128                 resolved_requires_md_review=bool(                                       
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        129                     getattr(resolved, "requires_md_review", False)                      
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        228                     requires_rn_review,                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        229                     requires_md_review,                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        302         resolved_requires_md_review: bool,                                              
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        341         requires_rn_review = any(                                                       
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        342             bool(row.get("requires_rn_review"))                                         
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        346         requires_md_review = (                                                          
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        347             resolved_requires_md_review                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        348             or any(bool(row.get("requires_md_review")) for row in group_results)        
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        390                 requires_md_review=requires_md_review,                                  
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        402             requires_rn_review=requires_rn_review,                                      
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        403             requires_md_review=requires_md_review,                                      
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        439                     requires_rn_review,                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        440                     requires_md_review,                                                 
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        444                     accepted_by,                                                        
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        445                     accepted_at,                                                        
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        446                     rejected_by,                                                        
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        447                     rejected_at,                                                        
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        448                     rejection_reason,                                                   
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        474                     :requires_rn_review,                                                
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        475                     :requires_md_review,                                                
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        515                 "requires_rn_review": candidate.requires_rn_review,                     
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        516                 "requires_md_review": candidate.requires_md_review,                     
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        655         requires_md_review: bool,                                                       
C:\dev\sns emr\backend\app\services\reasoning_result_to_recommendation_service.py        669         if requires_md_review:                                                          




## 11. chha_outcome_service.py Focused Context


  app\services\chha_outcome_service.py:6:
  app\services\chha_outcome_service.py:7:from fastapi import HTTPException
  app\services\chha_outcome_service.py:8:from sqlalchemy.orm import Session
  app\services\chha_outcome_service.py:9:
  app\services\chha_outcome_service.py:10:from app.models.visit import Visit
> app\services\chha_outcome_service.py:11:from app.models.task import Task
> app\services\chha_outcome_service.py:12:from app.models.enums import TaskType, TaskStatus, TaskRegulatoryBasis
> app\services\chha_outcome_service.py:13:from app.models.chha_visit_outcome import CHHAVisitOutcome
> app\services\chha_outcome_service.py:14:from app.models.chha_visit_task_result import CHHAVisitTaskResult
  app\services\chha_outcome_service.py:15:
  app\services\chha_outcome_service.py:16:
  app\services\chha_outcome_service.py:17:def upsert_chha_outcome(
  app\services\chha_outcome_service.py:18:    *,
  app\services\chha_outcome_service.py:19:    db: Session,
  app\services\chha_outcome_service.py:20:    visit: Visit,
  app\services\chha_outcome_service.py:21:    user_id: uuid.UUID,
  app\services\chha_outcome_service.py:22:    payload: Any,
> app\services\chha_outcome_service.py:23:) -> CHHAVisitOutcome:
  app\services\chha_outcome_service.py:24:    """
  app\services\chha_outcome_service.py:25:    Upserts structured CHHA outcome documentation for a single visit.
  app\services\chha_outcome_service.py:26:
  app\services\chha_outcome_service.py:27:    Behavior:
  app\services\chha_outcome_service.py:28:    - Valid only for CHHA/AIDE visits
  app\services\chha_outcome_service.py:29:    - Stores one outcome row per visit
> app\services\chha_outcome_service.py:30:    - Replaces child task result rows atomically on update
> app\services\chha_outcome_service.py:31:    - Creates or updates one RN follow-up task per CHHA visit when:
  app\services\chha_outcome_service.py:32:        * pain/change observed
  app\services\chha_outcome_service.py:33:        * condition changed
  app\services\chha_outcome_service.py:34:        * redness / breakdown noted
  app\services\chha_outcome_service.py:35:        * RN notification required
  app\services\chha_outcome_service.py:36:    """
  app\services\chha_outcome_service.py:43:            status_code=422,
  app\services\chha_outcome_service.py:44:            detail="CHHA outcome can only be recorded for AIDE/CHHA visits",
  app\services\chha_outcome_service.py:45:        )
  app\services\chha_outcome_service.py:46:
  app\services\chha_outcome_service.py:47:    outcome = (
> app\services\chha_outcome_service.py:48:        db.query(CHHAVisitOutcome)
> app\services\chha_outcome_service.py:49:        .filter(CHHAVisitOutcome.visit_id == visit.id)
  app\services\chha_outcome_service.py:50:        .first()
  app\services\chha_outcome_service.py:51:    )
  app\services\chha_outcome_service.py:52:
  app\services\chha_outcome_service.py:53:    now = datetime.now(timezone.utc)
  app\services\chha_outcome_service.py:54:
  app\services\chha_outcome_service.py:55:    if not outcome:
> app\services\chha_outcome_service.py:56:        outcome = CHHAVisitOutcome(
  app\services\chha_outcome_service.py:57:            tenant_id=visit.tenant_id,
  app\services\chha_outcome_service.py:58:            patient_id=visit.patient_id,
  app\services\chha_outcome_service.py:59:            visit_id=visit.id,
  app\services\chha_outcome_service.py:60:            created_by=user_id,
  app\services\chha_outcome_service.py:61:            created_at=now,
  app\services\chha_outcome_service.py:62:            updated_at=now,
  app\services\chha_outcome_service.py:63:        )
> app\services\chha_outcome_service.py:64:        db.add(outcome)
  app\services\chha_outcome_service.py:65:        db.flush()
  app\services\chha_outcome_service.py:66:
  app\services\chha_outcome_service.py:67:    # -------------------------------------------------
  app\services\chha_outcome_service.py:68:    # Update visit-level CHHA outcome
  app\services\chha_outcome_service.py:69:    # -------------------------------------------------
  app\services\chha_outcome_service.py:83:
  app\services\chha_outcome_service.py:84:    if payload.rn_notified:
  app\services\chha_outcome_service.py:85:        outcome.rn_notified_at = now
  app\services\chha_outcome_service.py:86:
  app\services\chha_outcome_service.py:87:    # -------------------------------------------------
> app\services\chha_outcome_service.py:88:    # Replace child task result rows deterministically
  app\services\chha_outcome_service.py:89:    # -------------------------------------------------
> app\services\chha_outcome_service.py:90:    db.query(CHHAVisitTaskResult).filter(
> app\services\chha_outcome_service.py:91:        CHHAVisitTaskResult.outcome_id == outcome.id
  app\services\chha_outcome_service.py:92:    ).delete()
  app\services\chha_outcome_service.py:93:
> app\services\chha_outcome_service.py:94:    for item in payload.task_results:
> app\services\chha_outcome_service.py:95:        db.add(
> app\services\chha_outcome_service.py:96:            CHHAVisitTaskResult(
  app\services\chha_outcome_service.py:97:                outcome_id=outcome.id,
  app\services\chha_outcome_service.py:98:                section_code=item.section_code,
> app\services\chha_outcome_service.py:99:                task_code=item.task_code,
  app\services\chha_outcome_service.py:100:                was_assigned=item.was_assigned,
  app\services\chha_outcome_service.py:101:                completed=item.completed,
  app\services\chha_outcome_service.py:102:                refused=item.refused,
  app\services\chha_outcome_service.py:103:                not_done=item.not_done,
  app\services\chha_outcome_service.py:104:                observation_code=item.observation_code,
  app\services\chha_outcome_service.py:118:        or payload.rn_notification_required
  app\services\chha_outcome_service.py:119:    )
  app\services\chha_outcome_service.py:120:
  app\services\chha_outcome_service.py:121:    if needs_rn_followup:
  app\services\chha_outcome_service.py:122:        # -------------------------------------------------
> app\services\chha_outcome_service.py:123:        # Derive urgency from CHHA findings
  app\services\chha_outcome_service.py:124:        # -------------------------------------------------
  app\services\chha_outcome_service.py:125:        if payload.skin_outcome == "BREAKDOWN":
  app\services\chha_outcome_service.py:126:            priority_value = "HIGH"
  app\services\chha_outcome_service.py:127:            severity_value = "HIGH"
  app\services\chha_outcome_service.py:128:        elif payload.skin_outcome == "REDNESS":
  app\services\chha_outcome_service.py:140:
  app\services\chha_outcome_service.py:141:        # -------------------------------------------------
  app\services\chha_outcome_service.py:142:        # ONE pending RN follow-up per VISIT (not per patient)
  app\services\chha_outcome_service.py:143:        # -------------------------------------------------
  app\services\chha_outcome_service.py:144:        query = (
> app\services\chha_outcome_service.py:145:            db.query(Task)
  app\services\chha_outcome_service.py:146:            .filter(
> app\services\chha_outcome_service.py:147:                Task.tenant_id == visit.tenant_id,
> app\services\chha_outcome_service.py:148:                Task.patient_id == visit.patient_id,
> app\services\chha_outcome_service.py:149:                Task.task_type == TaskType.CLINICAL_FOLLOWUP,
> app\services\chha_outcome_service.py:150:                Task.status == TaskStatus.PENDING,
  app\services\chha_outcome_service.py:151:            )
  app\services\chha_outcome_service.py:152:        )
  app\services\chha_outcome_service.py:153:
> app\services\chha_outcome_service.py:154:        if hasattr(Task, "alert_reason"):
> app\services\chha_outcome_service.py:155:            query = query.filter(Task.alert_reason == "CHHA_OUTCOME_ALERT")
  app\services\chha_outcome_service.py:156:
> app\services\chha_outcome_service.py:157:        if hasattr(Task, "reference_id"):
> app\services\chha_outcome_service.py:158:            query = query.filter(Task.reference_id == visit.id)
  app\services\chha_outcome_service.py:159:
  app\services\chha_outcome_service.py:160:        existing = query.first()
  app\services\chha_outcome_service.py:161:
  app\services\chha_outcome_service.py:162:        if existing:
  app\services\chha_outcome_service.py:163:            # -------------------------------------------------
  app\services\chha_outcome_service.py:168:
  app\services\chha_outcome_service.py:169:            if hasattr(existing, "origin"):
  app\services\chha_outcome_service.py:170:                existing.origin = "SYSTEM"
  app\services\chha_outcome_service.py:171:
  app\services\chha_outcome_service.py:172:            if hasattr(existing, "regulatory_basis"):
> app\services\chha_outcome_service.py:173:                existing.regulatory_basis = TaskRegulatoryBasis.CONDITION_TRIGGER
  app\services\chha_outcome_service.py:174:
  app\services\chha_outcome_service.py:175:            if hasattr(existing, "alert_reason"):
> app\services\chha_outcome_service.py:176:                existing.alert_reason = "CHHA_OUTCOME_ALERT"
  app\services\chha_outcome_service.py:177:
  app\services\chha_outcome_service.py:178:            if hasattr(existing, "priority"):
  app\services\chha_outcome_service.py:179:                existing.priority = priority_value
  app\services\chha_outcome_service.py:180:
  app\services\chha_outcome_service.py:181:            if hasattr(existing, "clinical_severity"):
  app\services\chha_outcome_service.py:204:
  app\services\chha_outcome_service.py:205:        else:
  app\services\chha_outcome_service.py:206:            # -------------------------------------------------
  app\services\chha_outcome_service.py:207:            # Create new RN alert for this visit
  app\services\chha_outcome_service.py:208:            # -------------------------------------------------
> app\services\chha_outcome_service.py:209:            task = Task(
  app\services\chha_outcome_service.py:210:                id=uuid.uuid4(),
  app\services\chha_outcome_service.py:211:                tenant_id=visit.tenant_id,
  app\services\chha_outcome_service.py:212:                patient_id=visit.patient_id,
> app\services\chha_outcome_service.py:213:                task_type=TaskType.CLINICAL_FOLLOWUP,
> app\services\chha_outcome_service.py:214:                status=TaskStatus.PENDING,
> app\services\chha_outcome_service.py:215:                regulatory_basis=TaskRegulatoryBasis.CONDITION_TRIGGER,
  app\services\chha_outcome_service.py:216:                due_date=now.date(),
  app\services\chha_outcome_service.py:217:                due_at=now,
  app\services\chha_outcome_service.py:218:                sla_start_at=now,
  app\services\chha_outcome_service.py:219:                sla_due_at=now + timedelta(hours=4),
  app\services\chha_outcome_service.py:220:                created_at=now,
  app\services\chha_outcome_service.py:221:                updated_at=now,
  app\services\chha_outcome_service.py:222:                created_by=user_id,
  app\services\chha_outcome_service.py:223:            )
  app\services\chha_outcome_service.py:224:
> app\services\chha_outcome_service.py:225:            if hasattr(task, "discipline"):
> app\services\chha_outcome_service.py:226:                task.discipline = "RN"
  app\services\chha_outcome_service.py:227:
> app\services\chha_outcome_service.py:228:            if hasattr(task, "origin"):
> app\services\chha_outcome_service.py:229:                task.origin = "SYSTEM"
  app\services\chha_outcome_service.py:230:
> app\services\chha_outcome_service.py:231:            if hasattr(task, "alert_reason"):
> app\services\chha_outcome_service.py:232:                task.alert_reason = "CHHA_OUTCOME_ALERT"
  app\services\chha_outcome_service.py:233:
> app\services\chha_outcome_service.py:234:            if hasattr(task, "priority"):
> app\services\chha_outcome_service.py:235:                task.priority = priority_value
  app\services\chha_outcome_service.py:236:
> app\services\chha_outcome_service.py:237:            if hasattr(task, "clinical_severity"):
> app\services\chha_outcome_service.py:238:                task.clinical_severity = severity_value
  app\services\chha_outcome_service.py:239:
> app\services\chha_outcome_service.py:240:            if hasattr(task, "reference_type"):
> app\services\chha_outcome_service.py:241:                task.reference_type = "VISIT"
  app\services\chha_outcome_service.py:242:
> app\services\chha_outcome_service.py:243:            if hasattr(task, "reference_id"):
> app\services\chha_outcome_service.py:244:                task.reference_id = visit.id
  app\services\chha_outcome_service.py:245:
> app\services\chha_outcome_service.py:246:            db.add(task)
  app\services\chha_outcome_service.py:247:
  app\services\chha_outcome_service.py:248:    return outcome




## 12. communications_log_service.py Focused Context


  app\services\communications_log_service.py:1:from datetime import datetime
  app\services\communications_log_service.py:2:from sqlalchemy.orm import Session
  app\services\communications_log_service.py:3:
  app\services\communications_log_service.py:4:from app.models.communications_log import CommunicationsLog
> app\services\communications_log_service.py:5:from app.services.communications_log_alerts import create_commlog_alerts
> app\services\communications_log_service.py:6:from app.services.commlog_to_task_bridge import handle_commlog_for_tasks
  app\services\communications_log_service.py:7:
  app\services\communications_log_service.py:8:
  app\services\communications_log_service.py:9:def create_communications_log_entry(
  app\services\communications_log_service.py:10:    *,
  app\services\communications_log_service.py:11:    db: Session,
  app\services\communications_log_service.py:26:        summary=payload.summary,
  app\services\communications_log_service.py:27:        details=payload.details,
  app\services\communications_log_service.py:28:        created_by=user_id,
  app\services\communications_log_service.py:29:    )
  app\services\communications_log_service.py:30:
> app\services\communications_log_service.py:31:    db.add(commlog)
  app\services\communications_log_service.py:32:    db.flush()  # ensures ID exists
  app\services\communications_log_service.py:33:
  app\services\communications_log_service.py:34:    # ------------------------------
  app\services\communications_log_service.py:35:    # ALERTS (safe)
  app\services\communications_log_service.py:36:    # ------------------------------
  app\services\communications_log_service.py:37:    try:
> app\services\communications_log_service.py:38:        create_commlog_alerts(
  app\services\communications_log_service.py:39:            db=db,
  app\services\communications_log_service.py:40:            patient_id=payload.patient_id,
  app\services\communications_log_service.py:41:            commlog_id=commlog.id,
  app\services\communications_log_service.py:42:            message=payload.summary,
  app\services\communications_log_service.py:43:            user_ids=[]  # placeholder for now
  app\services\communications_log_service.py:47:
  app\services\communications_log_service.py:48:    # ------------------------------
  app\services\communications_log_service.py:49:    # TASK BRIDGE (safe)
  app\services\communications_log_service.py:50:    # ------------------------------
  app\services\communications_log_service.py:51:    try:
> app\services\communications_log_service.py:52:        handle_commlog_for_tasks(db=db, commlog=commlog)
  app\services\communications_log_service.py:53:    except Exception:
  app\services\communications_log_service.py:54:        pass
  app\services\communications_log_service.py:55:
> app\services\communications_log_service.py:56:    db.commit()
> app\services\communications_log_service.py:57:    db.refresh(commlog)
  app\services\communications_log_service.py:58:
  app\services\communications_log_service.py:59:    return commlog




## 13. commlog_to_task_bridge.py Focused Context


  app\services\commlog_to_task_bridge.py:7:
  app\services\commlog_to_task_bridge.py:8:logger = logging.getLogger(__name__)
  app\services\commlog_to_task_bridge.py:9:
  app\services\commlog_to_task_bridge.py:10:
  app\services\commlog_to_task_bridge.py:11:# =========================================================
> app\services\commlog_to_task_bridge.py:12:# Communications Log -> Task Bridge
  app\services\commlog_to_task_bridge.py:13:# =========================================================
  app\services\commlog_to_task_bridge.py:14:#
  app\services\commlog_to_task_bridge.py:15:# Design goals:
  app\services\commlog_to_task_bridge.py:16:# - Must NEVER block comm log creation
  app\services\commlog_to_task_bridge.py:17:# - Must be best-effort and safe
> app\services\commlog_to_task_bridge.py:18:# - Must only create tasks for clinically relevant recipients
> app\services\commlog_to_task_bridge.py:19:# - Must avoid duplicate same-day follow-up tasks
  app\services\commlog_to_task_bridge.py:20:# - Must remain tenant-safe
  app\services\commlog_to_task_bridge.py:21:#
  app\services\commlog_to_task_bridge.py:22:# Trigger behavior:
> app\services\commlog_to_task_bridge.py:23:# - For CHANGE_OF_CONDITION reports, create CLINICAL_FOLLOWUP tasks
> app\services\commlog_to_task_bridge.py:24:# - Assign only to patient-linked clinical staff already known in tasks
> app\services\commlog_to_task_bridge.py:25:# - Do NOT create tasks for admin/DPCS here (they are notified, not task owners)
  app\services\commlog_to_task_bridge.py:26:# =========================================================
  app\services\commlog_to_task_bridge.py:27:
  app\services\commlog_to_task_bridge.py:28:
  app\services\commlog_to_task_bridge.py:29:CLINICAL_DISCIPLINES = {"RN", "LVN", "MSW", "BSW", "LCSW", "SC", "CHHA"}
  app\services\commlog_to_task_bridge.py:30:
  app\services\commlog_to_task_bridge.py:31:
> app\services\commlog_to_task_bridge.py:32:def _extract_trigger_type(commlog) -> str | None:
  app\services\commlog_to_task_bridge.py:33:    """
  app\services\commlog_to_task_bridge.py:34:    Safely extract trigger_type from details payload.
  app\services\commlog_to_task_bridge.py:35:    """
> app\services\commlog_to_task_bridge.py:36:    details = getattr(commlog, "details", None)
  app\services\commlog_to_task_bridge.py:37:
  app\services\commlog_to_task_bridge.py:38:    if isinstance(details, dict):
  app\services\commlog_to_task_bridge.py:39:        return details.get("trigger_type")
  app\services\commlog_to_task_bridge.py:40:
  app\services\commlog_to_task_bridge.py:41:    return None
  app\services\commlog_to_task_bridge.py:46:    *,
  app\services\commlog_to_task_bridge.py:47:    patient_id,
  app\services\commlog_to_task_bridge.py:48:    tenant_id,
  app\services\commlog_to_task_bridge.py:49:) -> list[tuple]:
  app\services\commlog_to_task_bridge.py:50:    """
> app\services\commlog_to_task_bridge.py:51:    Return distinct (assigned_user_id, discipline) pairs from existing task assignments.
  app\services\commlog_to_task_bridge.py:52:
  app\services\commlog_to_task_bridge.py:53:    This uses the current system reality:
> app\services\commlog_to_task_bridge.py:54:    - patient assignments are currently inferred from tasks
> app\services\commlog_to_task_bridge.py:55:    - only clinical disciplines should receive follow-up tasks
  app\services\commlog_to_task_bridge.py:56:    """
  app\services\commlog_to_task_bridge.py:57:    rows = db.execute(
  app\services\commlog_to_task_bridge.py:58:        text(
  app\services\commlog_to_task_bridge.py:59:            """
  app\services\commlog_to_task_bridge.py:60:            SELECT DISTINCT assigned_user_id, discipline::text
> app\services\commlog_to_task_bridge.py:61:            FROM tasks
  app\services\commlog_to_task_bridge.py:62:            WHERE patient_id = :patient_id
  app\services\commlog_to_task_bridge.py:63:              AND tenant_id = :tenant_id
  app\services\commlog_to_task_bridge.py:64:              AND assigned_user_id IS NOT NULL
  app\services\commlog_to_task_bridge.py:65:              AND discipline IN (
> app\services\commlog_to_task_bridge.py:66:                  'RN'::tasks_discipline_enum,
> app\services\commlog_to_task_bridge.py:67:                  'LVN'::tasks_discipline_enum,
> app\services\commlog_to_task_bridge.py:68:                  'MSW'::tasks_discipline_enum,
> app\services\commlog_to_task_bridge.py:69:                  'BSW'::tasks_discipline_enum,
> app\services\commlog_to_task_bridge.py:70:                  'LCSW'::tasks_discipline_enum,
> app\services\commlog_to_task_bridge.py:71:                  'SC'::tasks_discipline_enum,
> app\services\commlog_to_task_bridge.py:72:                  'CHHA'::tasks_discipline_enum
  app\services\commlog_to_task_bridge.py:73:              )
  app\services\commlog_to_task_bridge.py:74:            """
  app\services\commlog_to_task_bridge.py:75:        ),
  app\services\commlog_to_task_bridge.py:76:        {
  app\services\commlog_to_task_bridge.py:77:            "patient_id": patient_id,
  app\services\commlog_to_task_bridge.py:80:    ).fetchall()
  app\services\commlog_to_task_bridge.py:81:
  app\services\commlog_to_task_bridge.py:82:    return rows
  app\services\commlog_to_task_bridge.py:83:
  app\services\commlog_to_task_bridge.py:84:
> app\services\commlog_to_task_bridge.py:85:def _followup_task_exists_for_today(
  app\services\commlog_to_task_bridge.py:86:    db: Session,
  app\services\commlog_to_task_bridge.py:87:    *,
  app\services\commlog_to_task_bridge.py:88:    patient_id,
  app\services\commlog_to_task_bridge.py:89:    tenant_id,
  app\services\commlog_to_task_bridge.py:90:    assigned_user_id,
  app\services\commlog_to_task_bridge.py:91:    discipline: str,
> app\services\commlog_to_task_bridge.py:92:    commlog_id,
  app\services\commlog_to_task_bridge.py:93:) -> bool:
  app\services\commlog_to_task_bridge.py:94:    """
> app\services\commlog_to_task_bridge.py:95:    Prevent duplicate same-day follow-up tasks for the same comm log + assignee.
  app\services\commlog_to_task_bridge.py:96:    """
  app\services\commlog_to_task_bridge.py:97:    existing = db.execute(
  app\services\commlog_to_task_bridge.py:98:        text(
  app\services\commlog_to_task_bridge.py:99:            """
  app\services\commlog_to_task_bridge.py:100:            SELECT 1
> app\services\commlog_to_task_bridge.py:101:            FROM tasks
  app\services\commlog_to_task_bridge.py:102:            WHERE patient_id = :patient_id
  app\services\commlog_to_task_bridge.py:103:              AND tenant_id = :tenant_id
  app\services\commlog_to_task_bridge.py:104:              AND assigned_user_id = :assigned_user_id
> app\services\commlog_to_task_bridge.py:105:              AND discipline = CAST(:discipline AS tasks_discipline_enum)
> app\services\commlog_to_task_bridge.py:106:              AND task_type = 'CLINICAL_FOLLOWUP'::tasks_task_type_enum
> app\services\commlog_to_task_bridge.py:107:              AND origin = 'SYSTEM'::tasks_origin_enum
> app\services\commlog_to_task_bridge.py:108:              AND regulatory_basis = 'CONDITION_TRIGGER'::tasks_regulatory_basis_enum
  app\services\commlog_to_task_bridge.py:109:              AND due_date = CURRENT_DATE
  app\services\commlog_to_task_bridge.py:110:              AND alert_reason = :alert_reason
  app\services\commlog_to_task_bridge.py:111:              AND status IN (
> app\services\commlog_to_task_bridge.py:112:                    'PENDING'::tasks_status_enum,
> app\services\commlog_to_task_bridge.py:113:                    'OVERDUE'::tasks_status_enum,
> app\services\commlog_to_task_bridge.py:114:                    'ESCALATED'::tasks_status_enum
  app\services\commlog_to_task_bridge.py:115:              )
  app\services\commlog_to_task_bridge.py:116:            LIMIT 1
  app\services\commlog_to_task_bridge.py:117:            """
  app\services\commlog_to_task_bridge.py:118:        ),
  app\services\commlog_to_task_bridge.py:119:        {
  app\services\commlog_to_task_bridge.py:120:            "patient_id": patient_id,
  app\services\commlog_to_task_bridge.py:121:            "tenant_id": tenant_id,
  app\services\commlog_to_task_bridge.py:122:            "assigned_user_id": assigned_user_id,
  app\services\commlog_to_task_bridge.py:123:            "discipline": discipline,
> app\services\commlog_to_task_bridge.py:124:            "alert_reason": f"COMM_LOG:{commlog_id}",
  app\services\commlog_to_task_bridge.py:125:        },
  app\services\commlog_to_task_bridge.py:126:    ).fetchone()
  app\services\commlog_to_task_bridge.py:127:
  app\services\commlog_to_task_bridge.py:128:    return existing is not None
  app\services\commlog_to_task_bridge.py:129:
  app\services\commlog_to_task_bridge.py:130:
> app\services\commlog_to_task_bridge.py:131:def _create_followup_task(
  app\services\commlog_to_task_bridge.py:132:    db: Session,
  app\services\commlog_to_task_bridge.py:133:    *,
  app\services\commlog_to_task_bridge.py:134:    patient_id,
  app\services\commlog_to_task_bridge.py:135:    tenant_id,
  app\services\commlog_to_task_bridge.py:136:    assigned_user_id,
  app\services\commlog_to_task_bridge.py:137:    discipline: str,
> app\services\commlog_to_task_bridge.py:138:    commlog,
  app\services\commlog_to_task_bridge.py:139:) -> None:
  app\services\commlog_to_task_bridge.py:140:    """
> app\services\commlog_to_task_bridge.py:141:    Insert one follow-up task row.
  app\services\commlog_to_task_bridge.py:142:    """
  app\services\commlog_to_task_bridge.py:143:    db.execute(
  app\services\commlog_to_task_bridge.py:144:        text(
  app\services\commlog_to_task_bridge.py:145:            """
> app\services\commlog_to_task_bridge.py:146:            INSERT INTO tasks (
  app\services\commlog_to_task_bridge.py:147:                id,
  app\services\commlog_to_task_bridge.py:148:                patient_id,
  app\services\commlog_to_task_bridge.py:149:                assigned_user_id,
> app\services\commlog_to_task_bridge.py:150:                task_type,
  app\services\commlog_to_task_bridge.py:151:                origin,
  app\services\commlog_to_task_bridge.py:152:                discipline,
  app\services\commlog_to_task_bridge.py:153:                regulatory_basis,
  app\services\commlog_to_task_bridge.py:154:                due_date,
  app\services\commlog_to_task_bridge.py:155:                status,
  app\services\commlog_to_task_bridge.py:161:            )
  app\services\commlog_to_task_bridge.py:162:            VALUES (
  app\services\commlog_to_task_bridge.py:163:                :id,
  app\services\commlog_to_task_bridge.py:164:                :patient_id,
  app\services\commlog_to_task_bridge.py:165:                :assigned_user_id,
> app\services\commlog_to_task_bridge.py:166:                'CLINICAL_FOLLOWUP'::tasks_task_type_enum,
> app\services\commlog_to_task_bridge.py:167:                'SYSTEM'::tasks_origin_enum,
> app\services\commlog_to_task_bridge.py:168:                CAST(:discipline AS tasks_discipline_enum),
> app\services\commlog_to_task_bridge.py:169:                'CONDITION_TRIGGER'::tasks_regulatory_basis_enum,
  app\services\commlog_to_task_bridge.py:170:                CURRENT_DATE,
> app\services\commlog_to_task_bridge.py:171:                'PENDING'::tasks_status_enum,
  app\services\commlog_to_task_bridge.py:172:                NOW(),
  app\services\commlog_to_task_bridge.py:173:                NOW(),
  app\services\commlog_to_task_bridge.py:174:                :tenant_id,
  app\services\commlog_to_task_bridge.py:175:                :created_by,
  app\services\commlog_to_task_bridge.py:176:                :alert_reason
  app\services\commlog_to_task_bridge.py:181:            "id": uuid.uuid4(),
  app\services\commlog_to_task_bridge.py:182:            "patient_id": patient_id,
  app\services\commlog_to_task_bridge.py:183:            "assigned_user_id": assigned_user_id,
  app\services\commlog_to_task_bridge.py:184:            "discipline": discipline,
  app\services\commlog_to_task_bridge.py:185:            "tenant_id": tenant_id,
> app\services\commlog_to_task_bridge.py:186:            "created_by": getattr(commlog, "created_by", None),
> app\services\commlog_to_task_bridge.py:187:            "alert_reason": f"COMM_LOG:{commlog.id}",
  app\services\commlog_to_task_bridge.py:188:        },
  app\services\commlog_to_task_bridge.py:189:    )
  app\services\commlog_to_task_bridge.py:190:
  app\services\commlog_to_task_bridge.py:191:
> app\services\commlog_to_task_bridge.py:192:def handle_commlog_for_tasks(db: Session, commlog) -> None:
  app\services\commlog_to_task_bridge.py:193:    """
> app\services\commlog_to_task_bridge.py:194:    Best-effort task automation triggered by Communications Log events.
  app\services\commlog_to_task_bridge.py:195:
  app\services\commlog_to_task_bridge.py:196:    Current logic:
  app\services\commlog_to_task_bridge.py:197:    - If trigger_type == CHANGE_OF_CONDITION:
> app\services\commlog_to_task_bridge.py:198:        create CLINICAL_FOLLOWUP tasks for assigned clinical users
  app\services\commlog_to_task_bridge.py:199:    - If no patient clinical assignees are found:
  app\services\commlog_to_task_bridge.py:200:        log and exit safely
  app\services\commlog_to_task_bridge.py:201:    - Never commit here (router owns transaction)
  app\services\commlog_to_task_bridge.py:202:    """
  app\services\commlog_to_task_bridge.py:203:
> app\services\commlog_to_task_bridge.py:204:    patient_id = getattr(commlog, "patient_id", None)
> app\services\commlog_to_task_bridge.py:205:    tenant_id = getattr(commlog, "tenant_id", None)
  app\services\commlog_to_task_bridge.py:206:
  app\services\commlog_to_task_bridge.py:207:    if not patient_id or not tenant_id:
  app\services\commlog_to_task_bridge.py:208:        logger.warning(
> app\services\commlog_to_task_bridge.py:209:            "COMMLOG TASK BRIDGE SKIPPED: missing patient_id or tenant_id commlog_id=%s",
> app\services\commlog_to_task_bridge.py:210:            getattr(commlog, "id", None),
  app\services\commlog_to_task_bridge.py:211:        )
  app\services\commlog_to_task_bridge.py:212:        return
  app\services\commlog_to_task_bridge.py:213:
> app\services\commlog_to_task_bridge.py:214:    trigger_type = _extract_trigger_type(commlog)
  app\services\commlog_to_task_bridge.py:215:
  app\services\commlog_to_task_bridge.py:216:    if trigger_type != "CHANGE_OF_CONDITION":
  app\services\commlog_to_task_bridge.py:217:        logger.info(
> app\services\commlog_to_task_bridge.py:218:            "COMMLOG TASK BRIDGE SKIPPED: trigger_type=%s commlog_id=%s",
  app\services\commlog_to_task_bridge.py:219:            trigger_type,
> app\services\commlog_to_task_bridge.py:220:            getattr(commlog, "id", None),
  app\services\commlog_to_task_bridge.py:221:        )
  app\services\commlog_to_task_bridge.py:222:        return
  app\services\commlog_to_task_bridge.py:223:
  app\services\commlog_to_task_bridge.py:224:    assignees = _resolve_patient_clinical_assignees(
  app\services\commlog_to_task_bridge.py:225:        db,
  app\services\commlog_to_task_bridge.py:227:        tenant_id=tenant_id,
  app\services\commlog_to_task_bridge.py:228:    )
  app\services\commlog_to_task_bridge.py:229:
  app\services\commlog_to_task_bridge.py:230:    if not assignees:
  app\services\commlog_to_task_bridge.py:231:        logger.warning(
> app\services\commlog_to_task_bridge.py:232:            "COMMLOG TASK BRIDGE: no patient clinical assignees found patient_id=%s tenant_id=%s commlog_id=%s",
  app\services\commlog_to_task_bridge.py:233:            str(patient_id),
  app\services\commlog_to_task_bridge.py:234:            str(tenant_id),
> app\services\commlog_to_task_bridge.py:235:            str(getattr(commlog, "id", None)),
  app\services\commlog_to_task_bridge.py:236:        )
  app\services\commlog_to_task_bridge.py:237:        return
  app\services\commlog_to_task_bridge.py:238:
  app\services\commlog_to_task_bridge.py:239:    created_count = 0
  app\services\commlog_to_task_bridge.py:240:
  app\services\commlog_to_task_bridge.py:241:    for assigned_user_id, discipline in assignees:
  app\services\commlog_to_task_bridge.py:242:        if discipline not in CLINICAL_DISCIPLINES:
  app\services\commlog_to_task_bridge.py:243:            continue
  app\services\commlog_to_task_bridge.py:244:
> app\services\commlog_to_task_bridge.py:245:        if _followup_task_exists_for_today(
  app\services\commlog_to_task_bridge.py:246:            db,
  app\services\commlog_to_task_bridge.py:247:            patient_id=patient_id,
  app\services\commlog_to_task_bridge.py:248:            tenant_id=tenant_id,
  app\services\commlog_to_task_bridge.py:249:            assigned_user_id=assigned_user_id,
  app\services\commlog_to_task_bridge.py:250:            discipline=discipline,
> app\services\commlog_to_task_bridge.py:251:            commlog_id=commlog.id,
  app\services\commlog_to_task_bridge.py:252:        ):
  app\services\commlog_to_task_bridge.py:253:            continue
  app\services\commlog_to_task_bridge.py:254:
> app\services\commlog_to_task_bridge.py:255:        _create_followup_task(
  app\services\commlog_to_task_bridge.py:256:            db,
  app\services\commlog_to_task_bridge.py:257:            patient_id=patient_id,
  app\services\commlog_to_task_bridge.py:258:            tenant_id=tenant_id,
  app\services\commlog_to_task_bridge.py:259:            assigned_user_id=assigned_user_id,
  app\services\commlog_to_task_bridge.py:260:            discipline=discipline,
> app\services\commlog_to_task_bridge.py:261:            commlog=commlog,
  app\services\commlog_to_task_bridge.py:262:        )
  app\services\commlog_to_task_bridge.py:263:        created_count += 1
  app\services\commlog_to_task_bridge.py:264:
  app\services\commlog_to_task_bridge.py:265:    logger.info(
> app\services\commlog_to_task_bridge.py:266:        "COMMLOG TASK BRIDGE COMPLETE: patient_id=%s tenant_id=%s commlog_id=%s tasks_created=%s",
  app\services\commlog_to_task_bridge.py:267:        str(patient_id),
  app\services\commlog_to_task_bridge.py:268:        str(tenant_id),
> app\services\commlog_to_task_bridge.py:269:        str(commlog.id),
  app\services\commlog_to_task_bridge.py:270:        created_count,
  app\services\commlog_to_task_bridge.py:271:    )




## 14. clinical_reasoning_engine.py Focused Context


  app\services\clinical_reasoning_engine.py:11:from sqlalchemy import text
  app\services\clinical_reasoning_engine.py:12:from sqlalchemy.orm import Session
  app\services\clinical_reasoning_engine.py:13:
  app\services\clinical_reasoning_engine.py:14:
  app\services\clinical_reasoning_engine.py:15:@dataclass(frozen=True)
> app\services\clinical_reasoning_engine.py:16:class FindingCandidate:
  app\services\clinical_reasoning_engine.py:17:    category: str
  app\services\clinical_reasoning_engine.py:18:    finding_type: str
  app\services\clinical_reasoning_engine.py:19:    value_text: Optional[str] = None
  app\services\clinical_reasoning_engine.py:20:    value_numeric: Optional[Decimal] = None
  app\services\clinical_reasoning_engine.py:21:    previous_value_text: Optional[str] = None
  app\services\clinical_reasoning_engine.py:22:    previous_value_numeric: Optional[Decimal] = None
  app\services\clinical_reasoning_engine.py:23:    trend: Optional[str] = None
  app\services\clinical_reasoning_engine.py:24:    severity: Optional[str] = None
> app\services\clinical_reasoning_engine.py:25:    source: str = "RN"
  app\services\clinical_reasoning_engine.py:26:    observed_at: Optional[datetime] = None
> app\services\clinical_reasoning_engine.py:27:    is_significant_change: bool = False
  app\services\clinical_reasoning_engine.py:28:
  app\services\clinical_reasoning_engine.py:29:
  app\services\clinical_reasoning_engine.py:30:class ClinicalReasoningEngine:
  app\services\clinical_reasoning_engine.py:31:    """
  app\services\clinical_reasoning_engine.py:32:    Sprint 1 engine.
  app\services\clinical_reasoning_engine.py:34:    Responsibilities:
  app\services\clinical_reasoning_engine.py:35:    - Extract findings from assessment data.
  app\services\clinical_reasoning_engine.py:36:    - Save findings.
  app\services\clinical_reasoning_engine.py:37:    - Create significant-change events.
  app\services\clinical_reasoning_engine.py:38:    - Generate interpretations from configured database rules.
> app\services\clinical_reasoning_engine.py:39:    - Link interpretations to source findings.
  app\services\clinical_reasoning_engine.py:40:    """
  app\services\clinical_reasoning_engine.py:41:
  app\services\clinical_reasoning_engine.py:42:    GENERATED_BY = "engine"
  app\services\clinical_reasoning_engine.py:43:    DEFAULT_CONFIDENCE = "high"
  app\services\clinical_reasoning_engine.py:44:
  app\services\clinical_reasoning_engine.py:54:        if reset_existing:
  app\services\clinical_reasoning_engine.py:55:            self.delete_generated_outputs(db, reasoning_record_id)
  app\services\clinical_reasoning_engine.py:56:
  app\services\clinical_reasoning_engine.py:57:        findings = self.extract_findings(assessment_data)
  app\services\clinical_reasoning_engine.py:58:        inserted_findings = self.save_findings(db, reasoning_record_id, findings)
> app\services\clinical_reasoning_engine.py:59:        significant_changes = self.create_significant_change_events(
  app\services\clinical_reasoning_engine.py:60:            db, reasoning_record_id, inserted_findings
  app\services\clinical_reasoning_engine.py:61:        )
  app\services\clinical_reasoning_engine.py:62:        interpretations = self.generate_interpretations(db, reasoning_record_id)
  app\services\clinical_reasoning_engine.py:63:        
  app\services\clinical_reasoning_engine.py:64:        print(
  app\services\clinical_reasoning_engine.py:74:            db.commit()
  app\services\clinical_reasoning_engine.py:75:
  app\services\clinical_reasoning_engine.py:76:        return {
  app\services\clinical_reasoning_engine.py:77:            "reasoning_record_id": str(reasoning_record_id),
  app\services\clinical_reasoning_engine.py:78:            "findings_created": len(inserted_findings),
> app\services\clinical_reasoning_engine.py:79:            "significant_changes_created": len(significant_changes),
  app\services\clinical_reasoning_engine.py:80:            "interpretations_created": len(interpretations),
  app\services\clinical_reasoning_engine.py:81:            "reasoning_results_created": len(reasoning_results),
  app\services\clinical_reasoning_engine.py:82:            "findings": inserted_findings,
> app\services\clinical_reasoning_engine.py:83:            "significant_changes": significant_changes,
  app\services\clinical_reasoning_engine.py:84:            "interpretations": interpretations,
  app\services\clinical_reasoning_engine.py:85:            "reasoning_results": reasoning_results,
  app\services\clinical_reasoning_engine.py:86:        }
  app\services\clinical_reasoning_engine.py:87:
> app\services\clinical_reasoning_engine.py:88:    def extract_findings(self, assessment_data: Dict[str, Any]) -> List[FindingCandidate]:
> app\services\clinical_reasoning_engine.py:89:        source = assessment_data.get("source") or "RN"
  app\services\clinical_reasoning_engine.py:90:        observed_at = self._observed_at(assessment_data.get("observed_at"))
  app\services\clinical_reasoning_engine.py:91:
> app\services\clinical_reasoning_engine.py:92:        findings: List[FindingCandidate] = []
> app\services\clinical_reasoning_engine.py:93:        findings.extend(self._extract_weight_findings(assessment_data, source, observed_at))
> app\services\clinical_reasoning_engine.py:94:        findings.extend(self._extract_mac_findings(assessment_data, source, observed_at))
> app\services\clinical_reasoning_engine.py:95:        findings.extend(self._extract_appetite_findings(assessment_data, source, observed_at))
> app\services\clinical_reasoning_engine.py:96:        findings.extend(self._extract_pain_findings(assessment_data, source, observed_at))
> app\services\clinical_reasoning_engine.py:97:        findings.extend(self._extract_functional_findings(assessment_data, source, observed_at))
> app\services\clinical_reasoning_engine.py:98:        findings.extend(self._extract_safety_findings(assessment_data, source, observed_at))
> app\services\clinical_reasoning_engine.py:99:        findings.extend(self._extract_caregiver_findings(assessment_data, source, observed_at))
> app\services\clinical_reasoning_engine.py:100:        findings.extend(self._extract_respiratory_findings(assessment_data, source, observed_at))
> app\services\clinical_reasoning_engine.py:101:        findings.extend(self._extract_cardiac_findings(assessment_data, source, observed_at))
> app\services\clinical_reasoning_engine.py:102:        findings.extend(self._extract_cognitive_behavior_findings(assessment_data, source, observed_at))
> app\services\clinical_reasoning_engine.py:103:        findings.extend(self._extract_spiritual_findings(assessment_data, source, observed_at))
  app\services\clinical_reasoning_engine.py:104:
  app\services\clinical_reasoning_engine.py:105:        return self._dedupe_findings(findings)
  app\services\clinical_reasoning_engine.py:106:
> app\services\clinical_reasoning_engine.py:107:    def save_findings(
  app\services\clinical_reasoning_engine.py:108:        self,
  app\services\clinical_reasoning_engine.py:109:        db: Session,
  app\services\clinical_reasoning_engine.py:110:        reasoning_record_id: UUID,
> app\services\clinical_reasoning_engine.py:111:        findings: Iterable[FindingCandidate],
  app\services\clinical_reasoning_engine.py:112:    ) -> List[Dict[str, Any]]:
  app\services\clinical_reasoning_engine.py:113:        inserted: List[Dict[str, Any]] = []
  app\services\clinical_reasoning_engine.py:114:
  app\services\clinical_reasoning_engine.py:115:        for finding in findings:
  app\services\clinical_reasoning_engine.py:116:            row = db.execute(
  app\services\clinical_reasoning_engine.py:117:                text(
  app\services\clinical_reasoning_engine.py:118:                    """
> app\services\clinical_reasoning_engine.py:119:                    INSERT INTO findings (
  app\services\clinical_reasoning_engine.py:120:                        reasoning_record_id,
  app\services\clinical_reasoning_engine.py:121:                        category,
  app\services\clinical_reasoning_engine.py:122:                        finding_type,
  app\services\clinical_reasoning_engine.py:123:                        value_text,
  app\services\clinical_reasoning_engine.py:124:                        value_numeric,
  app\services\clinical_reasoning_engine.py:125:                        previous_value_text,
  app\services\clinical_reasoning_engine.py:126:                        previous_value_numeric,
  app\services\clinical_reasoning_engine.py:127:                        trend,
  app\services\clinical_reasoning_engine.py:128:                        severity,
> app\services\clinical_reasoning_engine.py:129:                        source,
  app\services\clinical_reasoning_engine.py:130:                        observed_at,
> app\services\clinical_reasoning_engine.py:131:                        is_significant_change
  app\services\clinical_reasoning_engine.py:132:                    )
  app\services\clinical_reasoning_engine.py:133:                    VALUES (
  app\services\clinical_reasoning_engine.py:134:                        :reasoning_record_id,
  app\services\clinical_reasoning_engine.py:135:                        :category,
  app\services\clinical_reasoning_engine.py:136:                        :finding_type,
  app\services\clinical_reasoning_engine.py:138:                        :value_numeric,
  app\services\clinical_reasoning_engine.py:139:                        :previous_value_text,
  app\services\clinical_reasoning_engine.py:140:                        :previous_value_numeric,
  app\services\clinical_reasoning_engine.py:141:                        :trend,
  app\services\clinical_reasoning_engine.py:142:                        :severity,
> app\services\clinical_reasoning_engine.py:143:                        :source,
  app\services\clinical_reasoning_engine.py:144:                        :observed_at,
> app\services\clinical_reasoning_engine.py:145:                        :is_significant_change
  app\services\clinical_reasoning_engine.py:146:                    )
  app\services\clinical_reasoning_engine.py:147:                    RETURNING
  app\services\clinical_reasoning_engine.py:148:                        id,
  app\services\clinical_reasoning_engine.py:149:                        category,
  app\services\clinical_reasoning_engine.py:150:                        finding_type,
  app\services\clinical_reasoning_engine.py:151:                        trend,
  app\services\clinical_reasoning_engine.py:152:                        severity,
> app\services\clinical_reasoning_engine.py:153:                        is_significant_change
  app\services\clinical_reasoning_engine.py:154:                    """
  app\services\clinical_reasoning_engine.py:155:                ),
  app\services\clinical_reasoning_engine.py:156:                {
  app\services\clinical_reasoning_engine.py:157:                    "reasoning_record_id": reasoning_record_id,
  app\services\clinical_reasoning_engine.py:158:                    "category": finding.category,
  app\services\clinical_reasoning_engine.py:161:                    "value_numeric": finding.value_numeric,
  app\services\clinical_reasoning_engine.py:162:                    "previous_value_text": finding.previous_value_text,
  app\services\clinical_reasoning_engine.py:163:                    "previous_value_numeric": finding.previous_value_numeric,
  app\services\clinical_reasoning_engine.py:164:                    "trend": finding.trend,
  app\services\clinical_reasoning_engine.py:165:                    "severity": finding.severity,
> app\services\clinical_reasoning_engine.py:166:                    "source": finding.source,
  app\services\clinical_reasoning_engine.py:167:                    "observed_at": finding.observed_at or datetime.now(timezone.utc),
> app\services\clinical_reasoning_engine.py:168:                    "is_significant_change": finding.is_significant_change,
  app\services\clinical_reasoning_engine.py:169:                },
  app\services\clinical_reasoning_engine.py:170:            ).mappings().one()
  app\services\clinical_reasoning_engine.py:171:
  app\services\clinical_reasoning_engine.py:172:            inserted.append(self._clean_row(dict(row)))
  app\services\clinical_reasoning_engine.py:173:
  app\services\clinical_reasoning_engine.py:174:        return inserted
  app\services\clinical_reasoning_engine.py:175:
> app\services\clinical_reasoning_engine.py:176:    def create_significant_change_events(
  app\services\clinical_reasoning_engine.py:177:        self,
  app\services\clinical_reasoning_engine.py:178:        db: Session,
  app\services\clinical_reasoning_engine.py:179:        reasoning_record_id: UUID,
  app\services\clinical_reasoning_engine.py:180:        inserted_findings: List[Dict[str, Any]],
  app\services\clinical_reasoning_engine.py:181:    ) -> List[Dict[str, Any]]:
  app\services\clinical_reasoning_engine.py:182:        created: List[Dict[str, Any]] = []
  app\services\clinical_reasoning_engine.py:183:
  app\services\clinical_reasoning_engine.py:184:        for finding in inserted_findings:
> app\services\clinical_reasoning_engine.py:185:            if not finding.get("is_significant_change"):
  app\services\clinical_reasoning_engine.py:186:                continue
  app\services\clinical_reasoning_engine.py:187:
  app\services\clinical_reasoning_engine.py:188:            row = db.execute(
  app\services\clinical_reasoning_engine.py:189:                text(
  app\services\clinical_reasoning_engine.py:190:                    """
> app\services\clinical_reasoning_engine.py:191:                    INSERT INTO significant_change_events (
  app\services\clinical_reasoning_engine.py:192:                        reasoning_record_id,
  app\services\clinical_reasoning_engine.py:193:                        finding_id,
  app\services\clinical_reasoning_engine.py:194:                        trigger_type,
  app\services\clinical_reasoning_engine.py:195:                        description,
  app\services\clinical_reasoning_engine.py:196:                        requires_notification,
  app\services\clinical_reasoning_engine.py:375:                    crr.id,
  app\services\clinical_reasoning_engine.py:376:                    crr.patient_id,
  app\services\clinical_reasoning_engine.py:377:                    crr.episode_id,
  app\services\clinical_reasoning_engine.py:378:                    crr.requires_poc_update,
  app\services\clinical_reasoning_engine.py:379:                    crr.requires_physician_review,
> app\services\clinical_reasoning_engine.py:380:                    crr.requires_idg_review,
  app\services\clinical_reasoning_engine.py:381:                    COALESCE(v.tenant_id, p.tenant_id) AS tenant_id
  app\services\clinical_reasoning_engine.py:382:                FROM clinical_reasoning_records crr
  app\services\clinical_reasoning_engine.py:383:                LEFT JOIN visits v
  app\services\clinical_reasoning_engine.py:384:                    ON v.id = crr.episode_id
  app\services\clinical_reasoning_engine.py:385:                LEFT JOIN patients p
  app\services\clinical_reasoning_engine.py:418:                text(
  app\services\clinical_reasoning_engine.py:419:                    """
  app\services\clinical_reasoning_engine.py:420:                    SELECT id
  app\services\clinical_reasoning_engine.py:421:                    FROM clinical_reasoning_results
  app\services\clinical_reasoning_engine.py:422:                    WHERE patient_id = :patient_id
> app\services\clinical_reasoning_engine.py:423:                    AND source_document_id = :source_document_id
  app\services\clinical_reasoning_engine.py:424:                    AND interpretation_key = :interpretation_key
  app\services\clinical_reasoning_engine.py:425:                    LIMIT 1
  app\services\clinical_reasoning_engine.py:426:                    """
  app\services\clinical_reasoning_engine.py:427:                ),
  app\services\clinical_reasoning_engine.py:428:                {
  app\services\clinical_reasoning_engine.py:429:                    "patient_id": record["patient_id"],
> app\services\clinical_reasoning_engine.py:430:                    "source_document_id": record["episode_id"],
  app\services\clinical_reasoning_engine.py:431:                    "interpretation_key": interpretation["interpretation_code"],
  app\services\clinical_reasoning_engine.py:432:                },
  app\services\clinical_reasoning_engine.py:433:            ).scalar_one_or_none()
  app\services\clinical_reasoning_engine.py:434:
  app\services\clinical_reasoning_engine.py:435:            if existing:
  app\services\clinical_reasoning_engine.py:446:                        f.value_numeric,
  app\services\clinical_reasoning_engine.py:447:                        f.previous_value_text,
  app\services\clinical_reasoning_engine.py:448:                        f.previous_value_numeric,
  app\services\clinical_reasoning_engine.py:449:                        f.trend,
  app\services\clinical_reasoning_engine.py:450:                        f.severity,
> app\services\clinical_reasoning_engine.py:451:                        f.source,
  app\services\clinical_reasoning_engine.py:452:                        f.observed_at,
> app\services\clinical_reasoning_engine.py:453:                        f.is_significant_change
  app\services\clinical_reasoning_engine.py:454:                    FROM interpretation_findings inf
  app\services\clinical_reasoning_engine.py:455:                    JOIN findings f
  app\services\clinical_reasoning_engine.py:456:                        ON f.id = inf.finding_id
  app\services\clinical_reasoning_engine.py:457:                    WHERE inf.interpretation_id = :interpretation_id
  app\services\clinical_reasoning_engine.py:458:                    ORDER BY f.observed_at ASC
  app\services\clinical_reasoning_engine.py:475:                            f.value_numeric,
  app\services\clinical_reasoning_engine.py:476:                            f.previous_value_text,
  app\services\clinical_reasoning_engine.py:477:                            f.previous_value_numeric,
  app\services\clinical_reasoning_engine.py:478:                            f.trend,
  app\services\clinical_reasoning_engine.py:479:                            f.severity,
> app\services\clinical_reasoning_engine.py:480:                            f.source,
  app\services\clinical_reasoning_engine.py:481:                            f.observed_at,
> app\services\clinical_reasoning_engine.py:482:                            f.is_significant_change
  app\services\clinical_reasoning_engine.py:483:                        FROM findings f
  app\services\clinical_reasoning_engine.py:484:                        WHERE f.reasoning_record_id = :reasoning_record_id
  app\services\clinical_reasoning_engine.py:485:                          AND f.finding_type IN (
  app\services\clinical_reasoning_engine.py:486:                              'pain_cause_category',
  app\services\clinical_reasoning_engine.py:487:                              'pain_cause_text',
  app\services\clinical_reasoning_engine.py:523:                        """
  app\services\clinical_reasoning_engine.py:524:                        INSERT INTO clinical_reasoning_results (
  app\services\clinical_reasoning_engine.py:525:                        id,
  app\services\clinical_reasoning_engine.py:526:                        tenant_id,
  app\services\clinical_reasoning_engine.py:527:                        patient_id,
> app\services\clinical_reasoning_engine.py:528:                        source_document_id,
> app\services\clinical_reasoning_engine.py:529:                        source_document_name,
  app\services\clinical_reasoning_engine.py:530:                        profile_key,
  app\services\clinical_reasoning_engine.py:531:                        interpretation_key,
  app\services\clinical_reasoning_engine.py:532:                        reasoning_category,
  app\services\clinical_reasoning_engine.py:533:                        severity_level,
  app\services\clinical_reasoning_engine.py:534:                        confidence,
  app\services\clinical_reasoning_engine.py:539:                        clinical_summary,
  app\services\clinical_reasoning_engine.py:540:                        recommended_diagnosis,
  app\services\clinical_reasoning_engine.py:541:                        recommended_icd10,
  app\services\clinical_reasoning_engine.py:542:                        requires_rn_review,
  app\services\clinical_reasoning_engine.py:543:                        requires_md_review,
> app\services\clinical_reasoning_engine.py:544:                        requires_idg_review,
  app\services\clinical_reasoning_engine.py:545:                        accepted_by,
  app\services\clinical_reasoning_engine.py:546:                        accepted_at,
  app\services\clinical_reasoning_engine.py:547:                        rejected_by,
  app\services\clinical_reasoning_engine.py:548:                        rejected_at,
  app\services\clinical_reasoning_engine.py:549:                        rejection_reason,
  app\services\clinical_reasoning_engine.py:552:                    )
  app\services\clinical_reasoning_engine.py:553:                    VALUES (
  app\services\clinical_reasoning_engine.py:554:                        gen_random_uuid(),
  app\services\clinical_reasoning_engine.py:555:                        :tenant_id,
  app\services\clinical_reasoning_engine.py:556:                        :patient_id,
> app\services\clinical_reasoning_engine.py:557:                        :source_document_id,
> app\services\clinical_reasoning_engine.py:558:                        :source_document_name,
  app\services\clinical_reasoning_engine.py:559:                        :profile_key,
  app\services\clinical_reasoning_engine.py:560:                        :interpretation_key,
  app\services\clinical_reasoning_engine.py:561:                        :reasoning_category,
  app\services\clinical_reasoning_engine.py:562:                        :severity_level,
  app\services\clinical_reasoning_engine.py:563:                        :confidence,
  app\services\clinical_reasoning_engine.py:568:                        :clinical_summary,
  app\services\clinical_reasoning_engine.py:569:                        :recommended_diagnosis,
  app\services\clinical_reasoning_engine.py:570:                        :recommended_icd10,
  app\services\clinical_reasoning_engine.py:571:                        :requires_rn_review,
  app\services\clinical_reasoning_engine.py:572:                        :requires_md_review,
> app\services\clinical_reasoning_engine.py:573:                        :requires_idg_review,
  app\services\clinical_reasoning_engine.py:574:                        NULL,
  app\services\clinical_reasoning_engine.py:575:                        NULL,
  app\services\clinical_reasoning_engine.py:576:                        NULL,
  app\services\clinical_reasoning_engine.py:577:                        NULL,
  app\services\clinical_reasoning_engine.py:578:                        NULL,
  app\services\clinical_reasoning_engine.py:587:                    """
  app\services\clinical_reasoning_engine.py:588:                    ),
  app\services\clinical_reasoning_engine.py:589:                    {
  app\services\clinical_reasoning_engine.py:590:                        "tenant_id": record["tenant_id"],
  app\services\clinical_reasoning_engine.py:591:                        "patient_id": record["patient_id"],
> app\services\clinical_reasoning_engine.py:592:                        "source_document_id": record["episode_id"],
> app\services\clinical_reasoning_engine.py:593:                        "source_document_name": "RN Visit Finalization",
  app\services\clinical_reasoning_engine.py:594:                        "profile_key": "RN_VISIT_REASONING",
  app\services\clinical_reasoning_engine.py:595:                        "interpretation_key": interpretation["interpretation_code"],
  app\services\clinical_reasoning_engine.py:596:                        "reasoning_category": str(
  app\services\clinical_reasoning_engine.py:597:                            interpretation["interpretation_code"] or ""
  app\services\clinical_reasoning_engine.py:598:                        ).lower(),
  app\services\clinical_reasoning_engine.py:605:                        "clinical_summary": interpretation["statement"],
  app\services\clinical_reasoning_engine.py:606:                        "recommended_diagnosis": recommended_diagnosis,
  app\services\clinical_reasoning_engine.py:607:                        "recommended_icd10": recommended_icd10,
  app\services\clinical_reasoning_engine.py:608:                        "requires_rn_review": requires_rn_review,
  app\services\clinical_reasoning_engine.py:609:                        "requires_md_review": bool(record["requires_physician_review"]),
> app\services\clinical_reasoning_engine.py:610:                        "requires_idg_review": bool(record["requires_idg_review"]),
  app\services\clinical_reasoning_engine.py:611:                        "reasoning_version": "clinical-reasoning-result-v1",
  app\services\clinical_reasoning_engine.py:612:                    },
  app\services\clinical_reasoning_engine.py:613:                ).mappings().one()
  app\services\clinical_reasoning_engine.py:614:
  app\services\clinical_reasoning_engine.py:615:                created.append(dict(row))
  app\services\clinical_reasoning_engine.py:637:        )
  app\services\clinical_reasoning_engine.py:638:
  app\services\clinical_reasoning_engine.py:639:        db.execute(
  app\services\clinical_reasoning_engine.py:640:            text(
  app\services\clinical_reasoning_engine.py:641:                """
> app\services\clinical_reasoning_engine.py:642:                DELETE FROM significant_change_events
  app\services\clinical_reasoning_engine.py:643:                WHERE reasoning_record_id = :reasoning_record_id
  app\services\clinical_reasoning_engine.py:644:                """
  app\services\clinical_reasoning_engine.py:645:            ),
  app\services\clinical_reasoning_engine.py:646:            {"reasoning_record_id": reasoning_record_id},
  app\services\clinical_reasoning_engine.py:647:        )
  app\services\clinical_reasoning_engine.py:671:                """
  app\services\clinical_reasoning_engine.py:672:                UPDATE clinical_reasoning_records
  app\services\clinical_reasoning_engine.py:673:                SET
  app\services\clinical_reasoning_engine.py:674:                    requires_poc_update = FALSE,
  app\services\clinical_reasoning_engine.py:675:                    requires_physician_review = FALSE,
> app\services\clinical_reasoning_engine.py:676:                    requires_idg_review = FALSE,
  app\services\clinical_reasoning_engine.py:677:                    updated_at = NOW()
  app\services\clinical_reasoning_engine.py:678:                WHERE id = :reasoning_record_id
  app\services\clinical_reasoning_engine.py:679:                """
  app\services\clinical_reasoning_engine.py:680:            ),
  app\services\clinical_reasoning_engine.py:681:            {"reasoning_record_id": reasoning_record_id},
  app\services\clinical_reasoning_engine.py:714:            db.commit()
  app\services\clinical_reasoning_engine.py:715:
  app\services\clinical_reasoning_engine.py:716:    def _extract_weight_findings(
  app\services\clinical_reasoning_engine.py:717:        self,
  app\services\clinical_reasoning_engine.py:718:        assessment_data: Dict[str, Any],
> app\services\clinical_reasoning_engine.py:719:        source: str,
  app\services\clinical_reasoning_engine.py:720:        observed_at: datetime,
> app\services\clinical_reasoning_engine.py:721:    ) -> List[FindingCandidate]:
  app\services\clinical_reasoning_engine.py:722:        weight = self._to_decimal(assessment_data.get("weight"))
  app\services\clinical_reasoning_engine.py:723:        previous_weight = self._to_decimal(assessment_data.get("previous_weight"))
  app\services\clinical_reasoning_engine.py:724:
  app\services\clinical_reasoning_engine.py:725:        if weight is None or previous_weight is None:
  app\services\clinical_reasoning_engine.py:726:            return []
  app\services\clinical_reasoning_engine.py:727:
  app\services\clinical_reasoning_engine.py:728:        if weight < previous_weight:
  app\services\clinical_reasoning_engine.py:729:            return [
> app\services\clinical_reasoning_engine.py:730:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:731:                    category="nutrition",
  app\services\clinical_reasoning_engine.py:732:                    finding_type="weight_loss",
  app\services\clinical_reasoning_engine.py:733:                    value_numeric=weight,
  app\services\clinical_reasoning_engine.py:734:                    previous_value_numeric=previous_weight,
  app\services\clinical_reasoning_engine.py:735:                    trend="declining",
> app\services\clinical_reasoning_engine.py:736:                    source=source,
  app\services\clinical_reasoning_engine.py:737:                    observed_at=observed_at,
> app\services\clinical_reasoning_engine.py:738:                    is_significant_change=True,
  app\services\clinical_reasoning_engine.py:739:                )
  app\services\clinical_reasoning_engine.py:740:            ]
  app\services\clinical_reasoning_engine.py:741:
  app\services\clinical_reasoning_engine.py:742:        if weight > previous_weight:
  app\services\clinical_reasoning_engine.py:743:            return [
> app\services\clinical_reasoning_engine.py:744:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:745:                    category="cardiac",
  app\services\clinical_reasoning_engine.py:746:                    finding_type="weight_gain",
  app\services\clinical_reasoning_engine.py:747:                    value_numeric=weight,
  app\services\clinical_reasoning_engine.py:748:                    previous_value_numeric=previous_weight,
  app\services\clinical_reasoning_engine.py:749:                    trend="worsening",
> app\services\clinical_reasoning_engine.py:750:                    source=source,
  app\services\clinical_reasoning_engine.py:751:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:752:                )
  app\services\clinical_reasoning_engine.py:753:            ]
  app\services\clinical_reasoning_engine.py:754:
  app\services\clinical_reasoning_engine.py:755:        return []
  app\services\clinical_reasoning_engine.py:756:
  app\services\clinical_reasoning_engine.py:757:    def _extract_mac_findings(
  app\services\clinical_reasoning_engine.py:758:        self,
  app\services\clinical_reasoning_engine.py:759:        assessment_data: Dict[str, Any],
> app\services\clinical_reasoning_engine.py:760:        source: str,
  app\services\clinical_reasoning_engine.py:761:        observed_at: datetime,
> app\services\clinical_reasoning_engine.py:762:    ) -> List[FindingCandidate]:
  app\services\clinical_reasoning_engine.py:763:        mac = self._to_decimal(assessment_data.get("mac"))
  app\services\clinical_reasoning_engine.py:764:        previous_mac = self._to_decimal(assessment_data.get("previous_mac"))
  app\services\clinical_reasoning_engine.py:765:
  app\services\clinical_reasoning_engine.py:766:        if mac is None or previous_mac is None:
  app\services\clinical_reasoning_engine.py:767:            return []
  app\services\clinical_reasoning_engine.py:768:
  app\services\clinical_reasoning_engine.py:769:        if mac < previous_mac:
  app\services\clinical_reasoning_engine.py:770:            return [
> app\services\clinical_reasoning_engine.py:771:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:772:                    category="nutrition",
  app\services\clinical_reasoning_engine.py:773:                    finding_type="mac_decline",
  app\services\clinical_reasoning_engine.py:774:                    value_numeric=mac,
  app\services\clinical_reasoning_engine.py:775:                    previous_value_numeric=previous_mac,
  app\services\clinical_reasoning_engine.py:776:                    trend="declining",
> app\services\clinical_reasoning_engine.py:777:                    source=source,
  app\services\clinical_reasoning_engine.py:778:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:779:                )
  app\services\clinical_reasoning_engine.py:780:            ]
  app\services\clinical_reasoning_engine.py:781:
  app\services\clinical_reasoning_engine.py:782:        return []
  app\services\clinical_reasoning_engine.py:783:
  app\services\clinical_reasoning_engine.py:784:    def _extract_appetite_findings(
  app\services\clinical_reasoning_engine.py:785:        self,
  app\services\clinical_reasoning_engine.py:786:        assessment_data: Dict[str, Any],
> app\services\clinical_reasoning_engine.py:787:        source: str,
  app\services\clinical_reasoning_engine.py:788:        observed_at: datetime,
> app\services\clinical_reasoning_engine.py:789:    ) -> List[FindingCandidate]:
  app\services\clinical_reasoning_engine.py:790:        appetite = assessment_data.get("appetite")
  app\services\clinical_reasoning_engine.py:791:        previous_appetite = assessment_data.get("previous_appetite")
  app\services\clinical_reasoning_engine.py:792:        appetite_decline = bool(assessment_data.get("appetite_decline"))
> app\services\clinical_reasoning_engine.py:793:        findings: List[FindingCandidate] = []
  app\services\clinical_reasoning_engine.py:794:
  app\services\clinical_reasoning_engine.py:795:        if appetite in {"poor", "none"}:
  app\services\clinical_reasoning_engine.py:796:            findings.append(
> app\services\clinical_reasoning_engine.py:797:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:798:                    category="nutrition",
  app\services\clinical_reasoning_engine.py:799:                    finding_type="poor_appetite",
  app\services\clinical_reasoning_engine.py:800:                    value_text=appetite,
  app\services\clinical_reasoning_engine.py:801:                    previous_value_text=previous_appetite,
  app\services\clinical_reasoning_engine.py:802:                    trend="declining",
> app\services\clinical_reasoning_engine.py:803:                    source=source,
  app\services\clinical_reasoning_engine.py:804:                    observed_at=observed_at,
> app\services\clinical_reasoning_engine.py:805:                    is_significant_change=appetite_decline,
  app\services\clinical_reasoning_engine.py:806:                )
  app\services\clinical_reasoning_engine.py:807:            )
  app\services\clinical_reasoning_engine.py:808:
  app\services\clinical_reasoning_engine.py:809:        if appetite_decline:
  app\services\clinical_reasoning_engine.py:810:            findings.append(
> app\services\clinical_reasoning_engine.py:811:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:812:                    category="nutrition",
> app\services\clinical_reasoning_engine.py:813:                    finding_type="significant_change_appetite",
  app\services\clinical_reasoning_engine.py:814:                    trend="declining",
> app\services\clinical_reasoning_engine.py:815:                    source=source,
  app\services\clinical_reasoning_engine.py:816:                    observed_at=observed_at,
> app\services\clinical_reasoning_engine.py:817:                    is_significant_change=True,
  app\services\clinical_reasoning_engine.py:818:                )
  app\services\clinical_reasoning_engine.py:819:            )
  app\services\clinical_reasoning_engine.py:820:
  app\services\clinical_reasoning_engine.py:821:        return findings
  app\services\clinical_reasoning_engine.py:822:
  app\services\clinical_reasoning_engine.py:823:    def _extract_pain_findings(
  app\services\clinical_reasoning_engine.py:824:        self,
  app\services\clinical_reasoning_engine.py:825:        assessment_data: Dict[str, Any],
> app\services\clinical_reasoning_engine.py:826:        source: str,
  app\services\clinical_reasoning_engine.py:827:        observed_at: datetime,
> app\services\clinical_reasoning_engine.py:828:    ) -> List[FindingCandidate]:
  app\services\clinical_reasoning_engine.py:829:        pain_score = self._to_decimal(assessment_data.get("pain_score"))
  app\services\clinical_reasoning_engine.py:830:        previous_pain_score = self._to_decimal(assessment_data.get("previous_pain_score"))
  app\services\clinical_reasoning_engine.py:831:        pain_increase = bool(assessment_data.get("pain_increase"))
> app\services\clinical_reasoning_engine.py:832:        findings: List[FindingCandidate] = []
  app\services\clinical_reasoning_engine.py:833:
  app\services\clinical_reasoning_engine.py:834:        if pain_score is not None:
  app\services\clinical_reasoning_engine.py:835:            trend = None
  app\services\clinical_reasoning_engine.py:836:            if previous_pain_score is not None and pain_score > previous_pain_score:
  app\services\clinical_reasoning_engine.py:837:                trend = "worsening"
  app\services\clinical_reasoning_engine.py:838:                pain_increase = True
  app\services\clinical_reasoning_engine.py:839:
  app\services\clinical_reasoning_engine.py:840:            findings.append(
> app\services\clinical_reasoning_engine.py:841:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:842:                    category="symptom",
  app\services\clinical_reasoning_engine.py:843:                    finding_type="pain",
  app\services\clinical_reasoning_engine.py:844:                    value_numeric=pain_score,
  app\services\clinical_reasoning_engine.py:845:                    previous_value_numeric=previous_pain_score,
  app\services\clinical_reasoning_engine.py:846:                    trend=trend,
  app\services\clinical_reasoning_engine.py:847:                    severity=self._pain_severity(pain_score),
> app\services\clinical_reasoning_engine.py:848:                    source=source,
  app\services\clinical_reasoning_engine.py:849:                    observed_at=observed_at,
> app\services\clinical_reasoning_engine.py:850:                    is_significant_change=pain_increase,
  app\services\clinical_reasoning_engine.py:851:                )
  app\services\clinical_reasoning_engine.py:852:            )
  app\services\clinical_reasoning_engine.py:853:
  app\services\clinical_reasoning_engine.py:854:        if pain_increase:
  app\services\clinical_reasoning_engine.py:855:            findings.append(
> app\services\clinical_reasoning_engine.py:856:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:857:                    category="symptom",
> app\services\clinical_reasoning_engine.py:858:                    finding_type="significant_change_pain",
  app\services\clinical_reasoning_engine.py:859:                    trend="worsening",
> app\services\clinical_reasoning_engine.py:860:                    source=source,
  app\services\clinical_reasoning_engine.py:861:                    observed_at=observed_at,
> app\services\clinical_reasoning_engine.py:862:                    is_significant_change=True,
  app\services\clinical_reasoning_engine.py:863:                )
  app\services\clinical_reasoning_engine.py:864:            )
  app\services\clinical_reasoning_engine.py:865:
  app\services\clinical_reasoning_engine.py:866:        # -------------------------------------------------
  app\services\clinical_reasoning_engine.py:867:        # Pain attribution / transcript-derived evidence
  app\services\clinical_reasoning_engine.py:868:        # -------------------------------------------------
  app\services\clinical_reasoning_engine.py:869:        pain_location = assessment_data.get("pain_location")
  app\services\clinical_reasoning_engine.py:870:        if pain_location:
  app\services\clinical_reasoning_engine.py:871:            findings.append(
> app\services\clinical_reasoning_engine.py:872:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:873:                    category="symptom",
  app\services\clinical_reasoning_engine.py:874:                    finding_type="pain_location",
  app\services\clinical_reasoning_engine.py:875:                    value_text=str(pain_location),
> app\services\clinical_reasoning_engine.py:876:                    source=source,
  app\services\clinical_reasoning_engine.py:877:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:878:                )
  app\services\clinical_reasoning_engine.py:879:            )
  app\services\clinical_reasoning_engine.py:880:
  app\services\clinical_reasoning_engine.py:881:        pain_quality = assessment_data.get("pain_quality")
  app\services\clinical_reasoning_engine.py:882:        if pain_quality:
  app\services\clinical_reasoning_engine.py:883:            findings.append(
> app\services\clinical_reasoning_engine.py:884:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:885:                    category="symptom",
  app\services\clinical_reasoning_engine.py:886:                    finding_type="pain_quality",
  app\services\clinical_reasoning_engine.py:887:                    value_text=str(pain_quality),
> app\services\clinical_reasoning_engine.py:888:                    source=source,
  app\services\clinical_reasoning_engine.py:889:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:890:                )
  app\services\clinical_reasoning_engine.py:891:            )
  app\services\clinical_reasoning_engine.py:892:
  app\services\clinical_reasoning_engine.py:893:        pain_cause_category = (
  app\services\clinical_reasoning_engine.py:895:            or assessment_data.get("cause_determination")
  app\services\clinical_reasoning_engine.py:896:        )
  app\services\clinical_reasoning_engine.py:897:
  app\services\clinical_reasoning_engine.py:898:        if pain_cause_category:
  app\services\clinical_reasoning_engine.py:899:            findings.append(
> app\services\clinical_reasoning_engine.py:900:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:901:                    category="symptom",
  app\services\clinical_reasoning_engine.py:902:                    finding_type="pain_cause_category",
  app\services\clinical_reasoning_engine.py:903:                    value_text=str(pain_cause_category),
> app\services\clinical_reasoning_engine.py:904:                    source=source,
  app\services\clinical_reasoning_engine.py:905:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:906:                )
  app\services\clinical_reasoning_engine.py:907:            )
  app\services\clinical_reasoning_engine.py:908:
  app\services\clinical_reasoning_engine.py:909:        pain_cause_text = (
  app\services\clinical_reasoning_engine.py:911:            or assessment_data.get("associated_diagnosis_text")
  app\services\clinical_reasoning_engine.py:912:        )
  app\services\clinical_reasoning_engine.py:913:
  app\services\clinical_reasoning_engine.py:914:        if pain_cause_text:
  app\services\clinical_reasoning_engine.py:915:            findings.append(
> app\services\clinical_reasoning_engine.py:916:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:917:                    category="symptom",
  app\services\clinical_reasoning_engine.py:918:                    finding_type="pain_cause_text",
  app\services\clinical_reasoning_engine.py:919:                    value_text=str(pain_cause_text),
> app\services\clinical_reasoning_engine.py:920:                    source=source,
  app\services\clinical_reasoning_engine.py:921:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:922:                )
  app\services\clinical_reasoning_engine.py:923:            )
  app\services\clinical_reasoning_engine.py:924:
  app\services\clinical_reasoning_engine.py:925:        assessment_summary = assessment_data.get("assessment_summary")
  app\services\clinical_reasoning_engine.py:926:        if assessment_summary:
  app\services\clinical_reasoning_engine.py:927:            findings.append(
> app\services\clinical_reasoning_engine.py:928:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:929:                    category="symptom",
  app\services\clinical_reasoning_engine.py:930:                    finding_type="assessment_summary",
  app\services\clinical_reasoning_engine.py:931:                    value_text=str(assessment_summary),
> app\services\clinical_reasoning_engine.py:932:                    source=source,
  app\services\clinical_reasoning_engine.py:933:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:934:                )
  app\services\clinical_reasoning_engine.py:935:            )
  app\services\clinical_reasoning_engine.py:936:
  app\services\clinical_reasoning_engine.py:937:        nursing_summary = assessment_data.get("nursing_summary")
  app\services\clinical_reasoning_engine.py:938:        if nursing_summary:
  app\services\clinical_reasoning_engine.py:939:            findings.append(
> app\services\clinical_reasoning_engine.py:940:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:941:                    category="symptom",
  app\services\clinical_reasoning_engine.py:942:                    finding_type="nursing_summary",
  app\services\clinical_reasoning_engine.py:943:                    value_text=str(nursing_summary),
> app\services\clinical_reasoning_engine.py:944:                    source=source,
  app\services\clinical_reasoning_engine.py:945:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:946:                )
  app\services\clinical_reasoning_engine.py:947:            )
  app\services\clinical_reasoning_engine.py:948:
  app\services\clinical_reasoning_engine.py:949:        return findings
  app\services\clinical_reasoning_engine.py:950:
  app\services\clinical_reasoning_engine.py:951:    def _extract_functional_findings(
  app\services\clinical_reasoning_engine.py:952:        self,
  app\services\clinical_reasoning_engine.py:953:        assessment_data: Dict[str, Any],
> app\services\clinical_reasoning_engine.py:954:        source: str,
  app\services\clinical_reasoning_engine.py:955:        observed_at: datetime,
> app\services\clinical_reasoning_engine.py:956:    ) -> List[FindingCandidate]:
> app\services\clinical_reasoning_engine.py:957:        findings: List[FindingCandidate] = []
  app\services\clinical_reasoning_engine.py:958:
  app\services\clinical_reasoning_engine.py:959:        if assessment_data.get("weakness_increased"):
  app\services\clinical_reasoning_engine.py:960:            findings.append(
> app\services\clinical_reasoning_engine.py:961:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:962:                    category="functional",
  app\services\clinical_reasoning_engine.py:963:                    finding_type="weakness",
  app\services\clinical_reasoning_engine.py:964:                    trend="worsening",
> app\services\clinical_reasoning_engine.py:965:                    source=source,
  app\services\clinical_reasoning_engine.py:966:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:967:                )
  app\services\clinical_reasoning_engine.py:968:            )
  app\services\clinical_reasoning_engine.py:969:
  app\services\clinical_reasoning_engine.py:970:        if assessment_data.get("mobility_decline"):
  app\services\clinical_reasoning_engine.py:971:            findings.append(
> app\services\clinical_reasoning_engine.py:972:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:973:                    category="functional",
  app\services\clinical_reasoning_engine.py:974:                    finding_type="mobility_decline",
  app\services\clinical_reasoning_engine.py:975:                    trend="declining",
> app\services\clinical_reasoning_engine.py:976:                    source=source,
  app\services\clinical_reasoning_engine.py:977:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:978:                )
  app\services\clinical_reasoning_engine.py:979:            )
  app\services\clinical_reasoning_engine.py:980:
  app\services\clinical_reasoning_engine.py:981:        if assessment_data.get("transfer_assistance_increased"):
  app\services\clinical_reasoning_engine.py:982:            findings.append(
> app\services\clinical_reasoning_engine.py:983:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:984:                    category="functional",
  app\services\clinical_reasoning_engine.py:985:                    finding_type="transfer_dependence",
  app\services\clinical_reasoning_engine.py:986:                    trend="worsening",
> app\services\clinical_reasoning_engine.py:987:                    source=source,
  app\services\clinical_reasoning_engine.py:988:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:989:                )
  app\services\clinical_reasoning_engine.py:990:            )
  app\services\clinical_reasoning_engine.py:991:
  app\services\clinical_reasoning_engine.py:992:        return findings
  app\services\clinical_reasoning_engine.py:993:
  app\services\clinical_reasoning_engine.py:994:    def _extract_safety_findings(
  app\services\clinical_reasoning_engine.py:995:        self,
  app\services\clinical_reasoning_engine.py:996:        assessment_data: Dict[str, Any],
> app\services\clinical_reasoning_engine.py:997:        source: str,
  app\services\clinical_reasoning_engine.py:998:        observed_at: datetime,
> app\services\clinical_reasoning_engine.py:999:    ) -> List[FindingCandidate]:
  app\services\clinical_reasoning_engine.py:1000:        fall_count = self._to_decimal(assessment_data.get("fall_count"))
  app\services\clinical_reasoning_engine.py:1001:
  app\services\clinical_reasoning_engine.py:1002:        if fall_count is None or fall_count <= 0:
  app\services\clinical_reasoning_engine.py:1003:            return []
  app\services\clinical_reasoning_engine.py:1004:
  app\services\clinical_reasoning_engine.py:1005:        return [
> app\services\clinical_reasoning_engine.py:1006:            FindingCandidate(
  app\services\clinical_reasoning_engine.py:1007:                category="safety",
  app\services\clinical_reasoning_engine.py:1008:                finding_type="fall",
  app\services\clinical_reasoning_engine.py:1009:                value_numeric=fall_count,
  app\services\clinical_reasoning_engine.py:1010:                trend="new",
> app\services\clinical_reasoning_engine.py:1011:                source=source,
  app\services\clinical_reasoning_engine.py:1012:                observed_at=observed_at,
> app\services\clinical_reasoning_engine.py:1013:                is_significant_change=True,
  app\services\clinical_reasoning_engine.py:1014:            )
  app\services\clinical_reasoning_engine.py:1015:        ]
  app\services\clinical_reasoning_engine.py:1016:
  app\services\clinical_reasoning_engine.py:1017:    def _extract_caregiver_findings(
  app\services\clinical_reasoning_engine.py:1018:        self,
  app\services\clinical_reasoning_engine.py:1019:        assessment_data: Dict[str, Any],
> app\services\clinical_reasoning_engine.py:1020:        source: str,
  app\services\clinical_reasoning_engine.py:1021:        observed_at: datetime,
> app\services\clinical_reasoning_engine.py:1022:    ) -> List[FindingCandidate]:
> app\services\clinical_reasoning_engine.py:1023:        findings: List[FindingCandidate] = []
  app\services\clinical_reasoning_engine.py:1024:
  app\services\clinical_reasoning_engine.py:1025:        if assessment_data.get("caregiver_tearful"):
  app\services\clinical_reasoning_engine.py:1026:            findings.append(
> app\services\clinical_reasoning_engine.py:1027:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:1028:                    category="caregiver",
  app\services\clinical_reasoning_engine.py:1029:                    finding_type="caregiver_distress",
  app\services\clinical_reasoning_engine.py:1030:                    trend="new",
> app\services\clinical_reasoning_engine.py:1031:                    source=source,
  app\services\clinical_reasoning_engine.py:1032:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:1033:                )
  app\services\clinical_reasoning_engine.py:1034:            )
  app\services\clinical_reasoning_engine.py:1035:
  app\services\clinical_reasoning_engine.py:1036:        if assessment_data.get("caregiver_overwhelmed"):
  app\services\clinical_reasoning_engine.py:1037:            findings.append(
> app\services\clinical_reasoning_engine.py:1038:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:1039:                    category="caregiver",
  app\services\clinical_reasoning_engine.py:1040:                    finding_type="caregiver_overwhelmed",
  app\services\clinical_reasoning_engine.py:1041:                    trend="new",
> app\services\clinical_reasoning_engine.py:1042:                    source=source,
  app\services\clinical_reasoning_engine.py:1043:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:1044:                )
  app\services\clinical_reasoning_engine.py:1045:            )
  app\services\clinical_reasoning_engine.py:1046:
  app\services\clinical_reasoning_engine.py:1047:        return findings
  app\services\clinical_reasoning_engine.py:1048:
  app\services\clinical_reasoning_engine.py:1049:    def _extract_respiratory_findings(
  app\services\clinical_reasoning_engine.py:1050:        self,
  app\services\clinical_reasoning_engine.py:1051:        assessment_data: Dict[str, Any],
> app\services\clinical_reasoning_engine.py:1052:        source: str,
  app\services\clinical_reasoning_engine.py:1053:        observed_at: datetime,
> app\services\clinical_reasoning_engine.py:1054:    ) -> List[FindingCandidate]:
> app\services\clinical_reasoning_engine.py:1055:        findings: List[FindingCandidate] = []
  app\services\clinical_reasoning_engine.py:1056:        respiratory_rate = self._to_decimal(assessment_data.get("respiratory_rate"))
  app\services\clinical_reasoning_engine.py:1057:        previous_respiratory_rate = self._to_decimal(
  app\services\clinical_reasoning_engine.py:1058:            assessment_data.get("previous_respiratory_rate")
  app\services\clinical_reasoning_engine.py:1059:        )
  app\services\clinical_reasoning_engine.py:1060:
  app\services\clinical_reasoning_engine.py:1062:            trend = None
  app\services\clinical_reasoning_engine.py:1063:            if previous_respiratory_rate is not None and respiratory_rate > previous_respiratory_rate:
  app\services\clinical_reasoning_engine.py:1064:                trend = "worsening"
  app\services\clinical_reasoning_engine.py:1065:
  app\services\clinical_reasoning_engine.py:1066:            findings.append(
> app\services\clinical_reasoning_engine.py:1067:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:1068:                    category="respiratory",
  app\services\clinical_reasoning_engine.py:1069:                    finding_type="tachypnea",
  app\services\clinical_reasoning_engine.py:1070:                    value_numeric=respiratory_rate,
  app\services\clinical_reasoning_engine.py:1071:                    previous_value_numeric=previous_respiratory_rate,
  app\services\clinical_reasoning_engine.py:1072:                    trend=trend,
> app\services\clinical_reasoning_engine.py:1073:                    source=source,
  app\services\clinical_reasoning_engine.py:1074:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:1075:                )
  app\services\clinical_reasoning_engine.py:1076:            )
  app\services\clinical_reasoning_engine.py:1077:
  app\services\clinical_reasoning_engine.py:1078:        if assessment_data.get("accessory_muscle_use"):
  app\services\clinical_reasoning_engine.py:1079:            findings.append(
> app\services\clinical_reasoning_engine.py:1080:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:1081:                    category="respiratory",
  app\services\clinical_reasoning_engine.py:1082:                    finding_type="accessory_muscle_use",
  app\services\clinical_reasoning_engine.py:1083:                    trend="new",
> app\services\clinical_reasoning_engine.py:1084:                    source=source,
  app\services\clinical_reasoning_engine.py:1085:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:1086:                )
  app\services\clinical_reasoning_engine.py:1087:            )
  app\services\clinical_reasoning_engine.py:1088:
  app\services\clinical_reasoning_engine.py:1089:        if assessment_data.get("oxygen_increase"):
  app\services\clinical_reasoning_engine.py:1090:            findings.append(
> app\services\clinical_reasoning_engine.py:1091:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:1092:                    category="respiratory",
  app\services\clinical_reasoning_engine.py:1093:                    finding_type="oxygen_increase",
  app\services\clinical_reasoning_engine.py:1094:                    trend="worsening",
> app\services\clinical_reasoning_engine.py:1095:                    source=source,
  app\services\clinical_reasoning_engine.py:1096:                    observed_at=observed_at,
> app\services\clinical_reasoning_engine.py:1097:                    is_significant_change=True,
  app\services\clinical_reasoning_engine.py:1098:                )
  app\services\clinical_reasoning_engine.py:1099:            )
  app\services\clinical_reasoning_engine.py:1100:
  app\services\clinical_reasoning_engine.py:1101:        return findings
  app\services\clinical_reasoning_engine.py:1102:
  app\services\clinical_reasoning_engine.py:1103:    def _extract_cardiac_findings(
  app\services\clinical_reasoning_engine.py:1104:        self,
  app\services\clinical_reasoning_engine.py:1105:        assessment_data: Dict[str, Any],
> app\services\clinical_reasoning_engine.py:1106:        source: str,
  app\services\clinical_reasoning_engine.py:1107:        observed_at: datetime,
> app\services\clinical_reasoning_engine.py:1108:    ) -> List[FindingCandidate]:
> app\services\clinical_reasoning_engine.py:1109:        findings: List[FindingCandidate] = []
  app\services\clinical_reasoning_engine.py:1110:
  app\services\clinical_reasoning_engine.py:1111:        if assessment_data.get("edema_present"):
  app\services\clinical_reasoning_engine.py:1112:            findings.append(
> app\services\clinical_reasoning_engine.py:1113:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:1114:                    category="cardiac",
  app\services\clinical_reasoning_engine.py:1115:                    finding_type="edema",
  app\services\clinical_reasoning_engine.py:1116:                    trend="worsening" if assessment_data.get("edema_worsening") else "new",
> app\services\clinical_reasoning_engine.py:1117:                    source=source,
  app\services\clinical_reasoning_engine.py:1118:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:1119:                )
  app\services\clinical_reasoning_engine.py:1120:            )
  app\services\clinical_reasoning_engine.py:1121:
  app\services\clinical_reasoning_engine.py:1122:        if assessment_data.get("orthopnea"):
  app\services\clinical_reasoning_engine.py:1123:            findings.append(
> app\services\clinical_reasoning_engine.py:1124:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:1125:                    category="cardiac",
  app\services\clinical_reasoning_engine.py:1126:                    finding_type="orthopnea",
  app\services\clinical_reasoning_engine.py:1127:                    trend="new",
> app\services\clinical_reasoning_engine.py:1128:                    source=source,
  app\services\clinical_reasoning_engine.py:1129:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:1130:                )
  app\services\clinical_reasoning_engine.py:1131:            )
  app\services\clinical_reasoning_engine.py:1132:
  app\services\clinical_reasoning_engine.py:1133:        return findings
  app\services\clinical_reasoning_engine.py:1134:
  app\services\clinical_reasoning_engine.py:1135:    def _extract_cognitive_behavior_findings(
  app\services\clinical_reasoning_engine.py:1136:        self,
  app\services\clinical_reasoning_engine.py:1137:        assessment_data: Dict[str, Any],
> app\services\clinical_reasoning_engine.py:1138:        source: str,
  app\services\clinical_reasoning_engine.py:1139:        observed_at: datetime,
> app\services\clinical_reasoning_engine.py:1140:    ) -> List[FindingCandidate]:
> app\services\clinical_reasoning_engine.py:1141:        findings: List[FindingCandidate] = []
  app\services\clinical_reasoning_engine.py:1142:
  app\services\clinical_reasoning_engine.py:1143:        if assessment_data.get("cognitive_decline"):
  app\services\clinical_reasoning_engine.py:1144:            findings.append(
> app\services\clinical_reasoning_engine.py:1145:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:1146:                    category="symptom",
  app\services\clinical_reasoning_engine.py:1147:                    finding_type="cognitive_decline",
  app\services\clinical_reasoning_engine.py:1148:                    trend="declining",
> app\services\clinical_reasoning_engine.py:1149:                    source=source,
  app\services\clinical_reasoning_engine.py:1150:                    observed_at=observed_at,
> app\services\clinical_reasoning_engine.py:1151:                    is_significant_change=True,
  app\services\clinical_reasoning_engine.py:1152:                )
  app\services\clinical_reasoning_engine.py:1153:            )
  app\services\clinical_reasoning_engine.py:1154:
  app\services\clinical_reasoning_engine.py:1155:        if assessment_data.get("behavior_change"):
  app\services\clinical_reasoning_engine.py:1156:            findings.append(
> app\services\clinical_reasoning_engine.py:1157:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:1158:                    category="symptom",
  app\services\clinical_reasoning_engine.py:1159:                    finding_type="behavior_change",
  app\services\clinical_reasoning_engine.py:1160:                    trend="new",
> app\services\clinical_reasoning_engine.py:1161:                    source=source,
  app\services\clinical_reasoning_engine.py:1162:                    observed_at=observed_at,
> app\services\clinical_reasoning_engine.py:1163:                    is_significant_change=True,
  app\services\clinical_reasoning_engine.py:1164:                )
  app\services\clinical_reasoning_engine.py:1165:            )
  app\services\clinical_reasoning_engine.py:1166:
  app\services\clinical_reasoning_engine.py:1167:        return findings
  app\services\clinical_reasoning_engine.py:1168:
  app\services\clinical_reasoning_engine.py:1169:    def _extract_spiritual_findings(
  app\services\clinical_reasoning_engine.py:1170:        self,
  app\services\clinical_reasoning_engine.py:1171:        assessment_data: Dict[str, Any],
> app\services\clinical_reasoning_engine.py:1172:        source: str,
  app\services\clinical_reasoning_engine.py:1173:        observed_at: datetime,
> app\services\clinical_reasoning_engine.py:1174:    ) -> List[FindingCandidate]:
> app\services\clinical_reasoning_engine.py:1175:        findings: List[FindingCandidate] = []
  app\services\clinical_reasoning_engine.py:1176:
  app\services\clinical_reasoning_engine.py:1177:        if assessment_data.get("spiritual_distress"):
  app\services\clinical_reasoning_engine.py:1178:            findings.append(
> app\services\clinical_reasoning_engine.py:1179:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:1180:                    category="spiritual",
  app\services\clinical_reasoning_engine.py:1181:                    finding_type="spiritual_distress",
  app\services\clinical_reasoning_engine.py:1182:                    trend="new",
> app\services\clinical_reasoning_engine.py:1183:                    source=source,
  app\services\clinical_reasoning_engine.py:1184:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:1185:                )
  app\services\clinical_reasoning_engine.py:1186:            )
  app\services\clinical_reasoning_engine.py:1187:
  app\services\clinical_reasoning_engine.py:1188:        if assessment_data.get("fear_of_dying"):
  app\services\clinical_reasoning_engine.py:1189:            findings.append(
> app\services\clinical_reasoning_engine.py:1190:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:1191:                    category="spiritual",
  app\services\clinical_reasoning_engine.py:1192:                    finding_type="fear_of_dying",
  app\services\clinical_reasoning_engine.py:1193:                    trend="new",
> app\services\clinical_reasoning_engine.py:1194:                    source=source,
  app\services\clinical_reasoning_engine.py:1195:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:1196:                )
  app\services\clinical_reasoning_engine.py:1197:            )
  app\services\clinical_reasoning_engine.py:1198:
  app\services\clinical_reasoning_engine.py:1199:        if assessment_data.get("hopelessness"):
  app\services\clinical_reasoning_engine.py:1200:            findings.append(
> app\services\clinical_reasoning_engine.py:1201:                FindingCandidate(
  app\services\clinical_reasoning_engine.py:1202:                    category="spiritual",
  app\services\clinical_reasoning_engine.py:1203:                    finding_type="hopelessness",
  app\services\clinical_reasoning_engine.py:1204:                    trend="new",
> app\services\clinical_reasoning_engine.py:1205:                    source=source,
  app\services\clinical_reasoning_engine.py:1206:                    observed_at=observed_at,
  app\services\clinical_reasoning_engine.py:1207:                )
  app\services\clinical_reasoning_engine.py:1208:            )
  app\services\clinical_reasoning_engine.py:1209:
  app\services\clinical_reasoning_engine.py:1210:        return findings
  app\services\clinical_reasoning_engine.py:1372:        if score >= Decimal("4"):
  app\services\clinical_reasoning_engine.py:1373:            return "moderate"
  app\services\clinical_reasoning_engine.py:1374:        return "mild"
  app\services\clinical_reasoning_engine.py:1375:
  app\services\clinical_reasoning_engine.py:1376:    @staticmethod
> app\services\clinical_reasoning_engine.py:1377:    def _dedupe_findings(findings: List[FindingCandidate]) -> List[FindingCandidate]:
  app\services\clinical_reasoning_engine.py:1378:        seen = set()
> app\services\clinical_reasoning_engine.py:1379:        result: List[FindingCandidate] = []
  app\services\clinical_reasoning_engine.py:1380:
  app\services\clinical_reasoning_engine.py:1381:        for finding in findings:
  app\services\clinical_reasoning_engine.py:1382:            key = (
  app\services\clinical_reasoning_engine.py:1383:                finding.category,
  app\services\clinical_reasoning_engine.py:1384:                finding.finding_type,




## 15. visits.py Clinical Reasoning Entry Points


  app\api\visits.py:36:from app.models.visit import Visit
  app\api\visits.py:37:from app.models.med_reconciliation import MedReconciliationItem
  app\api\visits.py:38:from app.models.sfv_requirement import SFVRequirement
  app\api\visits.py:39:from app.models.admission import Admission
  app\api\visits.py:40:
> app\api\visits.py:41:from app.services.chha_outcome_service import upsert_chha_outcome
  app\api\visits.py:42:from app.services.diagnosis_sync_service import sync_official_primary_diagnosis
  app\api\visits.py:43:from app.services.audit_logger import log_event
  app\api\visits.py:44:from app.services.bereavement_aggregation_engine import (
  app\api\visits.py:45:    BereavementAggregationEngine,
  app\api\visits.py:46:    BereavementNoteInput,
  app\api\visits.py:58:from app.services.hope_phase_b_engine import (
  app\api\visits.py:59:    complete_sfv_requirement_from_visit,
  app\api\visits.py:60:    process_huv_finalize,
  app\api\visits.py:61:    process_initial_rn_ica_finalize,
  app\api\visits.py:62:)
> app\api\visits.py:63:from app.services.clinical_reasoning_engine import ClinicalReasoningEngine
  app\api\visits.py:64:from app.services.reasoning_result_to_recommendation_service import (
  app\api\visits.py:65:    ReasoningResultToRecommendationService,
  app\api\visits.py:66:)
  app\api\visits.py:67:
  app\api\visits.py:68:logger = logging.getLogger(__name__)
  app\api\visits.py:140:# ENGINE SINGLETONS
  app\api\visits.py:141:# =========================================================
  app\api\visits.py:142:
  app\api\visits.py:143:condition_engine = DynamicConditionDetectionEngine()
  app\api\visits.py:144:bereavement_engine = BereavementAggregationEngine()
> app\api\visits.py:145:clinical_reasoning_engine = ClinicalReasoningEngine()
  app\api\visits.py:146:reasoning_recommendation_service = ReasoningResultToRecommendationService()
  app\api\visits.py:147:
  app\api\visits.py:148:# =========================================================
  app\api\visits.py:149:# DB DEPENDENCY
  app\api\visits.py:150:# =========================================================
  app\api\visits.py:342:    not_done: bool = False
  app\api\visits.py:343:    observation_code: Optional[str] = None
  app\api\visits.py:344:    result_note: Optional[str] = None
  app\api\visits.py:345:
  app\api\visits.py:346:
> app\api\visits.py:347:class CHHAOutcomeUpsertRequest(BaseModel):
  app\api\visits.py:348:    poc_reference_id: Optional[uuid.UUID] = None
  app\api\visits.py:349:    tolerance_to_care: str
  app\api\visits.py:350:    condition_during_visit: str
  app\api\visits.py:351:    skin_outcome: str
  app\api\visits.py:352:
  app\api\visits.py:578:        if issue_present:
  app\api\visits.py:579:            raise HTTPException(
  app\api\visits.py:580:                status_code=422,
  app\api\visits.py:581:                detail=(
  app\api\visits.py:582:                    "SW psychosocial visits should not use nursing issue event types. "
> app\api\visits.py:583:                    "Keep ROUTINE_VISIT and document psychosocial findings in the SW routine form."
  app\api\visits.py:584:                ),
  app\api\visits.py:585:            )
  app\api\visits.py:586:        return
  app\api\visits.py:587:
  app\api\visits.py:588:    if form_type == VisitFormType.SHORT_FORM.value:
  app\api\visits.py:2534:        ),
  app\api\visits.py:2535:    }
  app\api\visits.py:2536:
  app\api\visits.py:2537:
  app\api\visits.py:2538:@router.post("/{visit_id}/chha-outcome")
> app\api\visits.py:2539:def upsert_chha_visit_outcome(
  app\api\visits.py:2540:    visit_id: uuid.UUID,
> app\api\visits.py:2541:    payload: CHHAOutcomeUpsertRequest,
  app\api\visits.py:2542:    request: Request,
  app\api\visits.py:2543:    response: Response,
  app\api\visits.py:2544:    db: Session = Depends(get_db),
  app\api\visits.py:2545:):
  app\api\visits.py:2546:    # =========================================================
  app\api\visits.py:2593:
  app\api\visits.py:2594:    # =========================================================
  app\api\visits.py:2595:    # UPSERT OUTCOME
  app\api\visits.py:2596:    # =========================================================
  app\api\visits.py:2597:    try:
> app\api\visits.py:2598:        outcome = upsert_chha_outcome(
  app\api\visits.py:2599:            db=db,
  app\api\visits.py:2600:            visit=visit,
  app\api\visits.py:2601:            user_id=user_id,
  app\api\visits.py:2602:            payload=payload,
  app\api\visits.py:2603:        )
  app\api\visits.py:2606:        # AUDIT LOG (REQUIRED)
  app\api\visits.py:2607:        # =====================================================
  app\api\visits.py:2608:        _safe_log_event(
  app\api\visits.py:2609:            db=db,
  app\api\visits.py:2610:            user_id=user_id,
> app\api\visits.py:2611:            action="UPSERT_CHHA_OUTCOME",
  app\api\visits.py:2612:            entity_type="visit",
  app\api\visits.py:2613:            entity_id=visit.id,
  app\api\visits.py:2614:            request_id=request_id,
  app\api\visits.py:2615:            metadata={
  app\api\visits.py:2616:                "visit_id": str(visit.id),
  app\api\visits.py:2925:    )
  app\api\visits.py:2926:    
  app\api\visits.py:2927:    return payload
  app\api\visits.py:2928:
  app\api\visits.py:2929:
> app\api\visits.py:2930:def _get_or_create_clinical_reasoning_record_for_visit(
  app\api\visits.py:2931:    db: Session,
  app\api\visits.py:2932:    visit: Visit,
  app\api\visits.py:2933:) -> uuid.UUID:
  app\api\visits.py:2934:    existing = db.execute(
  app\api\visits.py:2935:        text(
  app\api\visits.py:2981:    ).scalar_one()
  app\api\visits.py:2982:
  app\api\visits.py:2983:    return created
  app\api\visits.py:2984:
  app\api\visits.py:2985:
> app\api\visits.py:2986:def _run_clinical_reasoning_for_visit(
  app\api\visits.py:2987:    db: Session,
  app\api\visits.py:2988:    visit: Visit,
  app\api\visits.py:2989:    notes: list[ClinicalNote],
  app\api\visits.py:2990:    request_id: str,
  app\api\visits.py:2991:) -> None:
  app\api\visits.py:3005:            str(visit.id),
  app\api\visits.py:3006:            request_id,
  app\api\visits.py:3007:        )
  app\api\visits.py:3008:        return
  app\api\visits.py:3009:
> app\api\visits.py:3010:    reasoning_record_id = _get_or_create_clinical_reasoning_record_for_visit(
  app\api\visits.py:3011:        db=db,
  app\api\visits.py:3012:        visit=visit,
  app\api\visits.py:3013:    )
  app\api\visits.py:3014:
> app\api\visits.py:3015:    result = clinical_reasoning_engine.process_assessment(
  app\api\visits.py:3016:        db=db,
  app\api\visits.py:3017:        reasoning_record_id=reasoning_record_id,
  app\api\visits.py:3018:        assessment_data=assessment_payload,
  app\api\visits.py:3019:        reset_existing=True,
  app\api\visits.py:3020:        commit=False,
  app\api\visits.py:3305:            logger.info(
  app\api\visits.py:3306:                "FINALIZE: BEFORE_CLINICAL_REASONING visit_id=%s request_id=%s",
  app\api\visits.py:3307:                str(visit.id),
  app\api\visits.py:3308:                request_id,
  app\api\visits.py:3309:            )
> app\api\visits.py:3310:            _run_clinical_reasoning_for_visit(
  app\api\visits.py:3311:                db=db,
  app\api\visits.py:3312:                visit=visit,
  app\api\visits.py:3313:                notes=notes,
  app\api\visits.py:3314:                request_id=request_id,
  app\api\visits.py:3315:            )




## 16. DB Tables Matching UCIER Terms

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND (
    table_name ILIKE '%evidence%'
    OR table_name ILIKE '%finding%'
    OR table_name ILIKE '%reason%'
    OR table_name ILIKE '%interpret%'
    OR table_name ILIKE '%problem%'
    OR table_name ILIKE '%note%'
    OR table_name ILIKE '%visit%'
    OR table_name ILIKE '%comm%'
    OR table_name ILIKE '%chha%'
    OR table_name ILIKE '%idg%'
)
ORDER BY table_name;


## 17. clinical_notes Constraints

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT
    conname,
    pg_get_constraintdef(oid) AS constraint_definition
FROM pg_constraint
WHERE conrelid = 'clinical_notes'::regclass
ORDER BY conname;


## 18. communications_logs Columns

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'communications_logs'
ORDER BY ordinal_position;


## 19. episode_evidence Columns

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'episode_evidence'
ORDER BY ordinal_position;


## 20. episode_evidence Current Source Types

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT
    evidence_source_type,
    discipline,
    COUNT(*) AS count
FROM episode_evidence
GROUP BY evidence_source_type, discipline
ORDER BY count DESC;


## 21. episode_evidence Foreign Keys

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name = 'episode_evidence'
ORDER BY tc.table_name, kcu.column_name;


## 22. findings Columns

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'findings'
ORDER BY ordinal_position;


## 23. significant_change_events Columns

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'significant_change_events'
ORDER BY ordinal_position;


## 24. clinical_reasoning_results Columns

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'clinical_reasoning_results'
ORDER BY ordinal_position;


## 25. CHHA Table Columns

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name IN (
    'chha_visit_outcomes',
    'chha_visit_task_results',
    'chha_pocs'
)
ORDER BY table_name, ordinal_position;


## 26. CHHA Row Counts

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT
    'chha_visit_outcomes' AS table_name,
    COUNT(*) AS row_count
FROM chha_visit_outcomes
UNION ALL
SELECT
    'chha_visit_task_results' AS table_name,
    COUNT(*) AS row_count
FROM chha_visit_task_results
UNION ALL
SELECT
    'chha_pocs' AS table_name,
    COUNT(*) AS row_count
FROM chha_pocs;


## 27. Communication Log Row Counts by Status and Type

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT
    status,
    event_type,
    focus_area,
    COUNT(*) AS row_count
FROM communications_logs
GROUP BY status, event_type, focus_area
ORDER BY row_count DESC;


## 28. IDG Tables

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name ILIKE '%idg%'
ORDER BY table_name;


## 29. Task Columns Related to Evidence and References

PSQL NOT FOUND ON PATH. Run this SQL manually:

SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'tasks'
AND (
    column_name ILIKE '%evidence%'
    OR column_name ILIKE '%reference%'
    OR column_name ILIKE '%reason%'
    OR column_name ILIKE '%status%'
    OR column_name ILIKE '%task%'
    OR column_name ILIKE '%discipline%'
    OR column_name ILIKE '%alert%'
)
ORDER BY ordinal_position;


## 30. Discovery Interpretation Checklist

Use this checklist to classify the implementation path:

[ ] communications_logs -> episode_evidence exists
[ ] communications_logs -> findings exists
[ ] communications_logs -> clinical_reasoning exists
[ ] chha_visit_outcomes -> episode_evidence exists
[ ] chha_visit_outcomes -> findings exists
[ ] chha_visit_outcomes -> RN task exists
[ ] clinical_reasoning_results.requires_idg_review triggers IDG workflow
[ ] episode_evidence appears in IDG dashboard/review
[ ] findings appear in IDG dashboard/review
[ ] tasks support evidence_ref_type and evidence_ref_id
[ ] CHHA remains observational only, no direct diagnostic interpretation
[ ] communication log can become observation evidence for RN/IDG discussion

## 31. Recommended Classification Rules

DO NOT create new tables until reuse is ruled out:

Do not create patient_evidence_registry until episode_evidence is confirmed insufficient.
Do not create patient_signal_registry until findings is confirmed insufficient.
Do not create a new IDG queue until existing IDG review/task/dashboard paths are confirmed insufficient.
Do not make CHHA create clinical findings directly.
Do allow CHHA and communication-log content to create observation evidence candidates.
Do require RN/LVN/IDG review before clinical interpretation.

## 32. End of Packet

Discovery packet complete.
Output file: C:\dev\sns emr\backend\SNS_UCIER_DISCOVERY_PACKET.md
