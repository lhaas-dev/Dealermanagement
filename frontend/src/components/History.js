import React, { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Archive, Calendar, Car, CheckCircle, XCircle, Camera, FileText, Eye, Trash2 } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const History = ({ user, authToken }) => {
  const [archives, setArchives] = useState([]);
  const [selectedArchive, setSelectedArchive] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showArchiveDialog, setShowArchiveDialog] = useState(false);
  const [showArchiveDetailsDialog, setShowArchiveDetailsDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showDeleteAllDialog, setShowDeleteAllDialog] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [deleteAllConfirmation, setDeleteAllConfirmation] = useState('');
  const [archiveToDelete, setArchiveToDelete] = useState(null);
  const [archiveFormData, setArchiveFormData] = useState({
    archive_name: "",
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear()
  });

  useEffect(() => {
    fetchArchives();
  }, []);

  const fetchArchives = async () => {
    try {
      const response = await axios.get(`${API}/archives`);
      setArchives(response.data);
    } catch (error) {
      console.error('Error fetching archives:', error);
      toast.error('Failed to fetch archives');
    } finally {
      setLoading(false);
    }
  };

  const createMonthlyArchive = async () => {
    if (!archiveFormData.archive_name.trim()) {
      toast.error('Bitte geben Sie einen Archiv-Namen ein');
      return;
    }

    try {
      const response = await axios.post(`${API}/archives/create-monthly`, archiveFormData);
      const result = response.data;
      toast.success(`Archiv "${result.archive_name}" erfolgreich erstellt mit ${result.total_cars} Fahrzeugen`);
      setShowArchiveDialog(false);
      setArchiveFormData({
        archive_name: "",
        month: new Date().getMonth() + 1,
        year: new Date().getFullYear()
      });
      
      // Refresh archives
      await fetchArchives();
    } catch (error) {
      console.error('Error creating archive:', error);
      toast.error('Fehler beim Erstellen des Archivs: ' + (error.response?.data?.detail || error.message));
    }
  };

  const deleteArchive = async () => {
    if (deleteConfirmation !== 'LÖSCHEN') {
      toast.error('Bitte geben Sie "LÖSCHEN" ein, um zu bestätigen');
      return;
    }

    if (!archiveToDelete) return;

    try {
      await axios.delete(`${API}/archives/${archiveToDelete.id}`);
      toast.success(`Archiv "${archiveToDelete.archive_name}" wurde erfolgreich gelöscht`);
      
      setShowDeleteDialog(false);
      setDeleteConfirmation('');
      setArchiveToDelete(null);
      
      // Refresh archives
      await fetchArchives();
    } catch (error) {
      console.error('Error deleting archive:', error);
      toast.error('Fehler beim Löschen des Archivs: ' + (error.response?.data?.detail || error.message));
    }
  };

  const deleteAllArchives = async () => {
    if (deleteAllConfirmation !== 'LÖSCHEN') {
      toast.error('Bitte geben Sie "LÖSCHEN" ein, um zu bestätigen');
      return;
    }

    try {
      const response = await axios.delete(`${API}/archives`);
      const result = response.data;
      toast.success(`Alle Archive wurden erfolgreich gelöscht (${result.deleted_count} Archive)`);
      
      setShowDeleteAllDialog(false);
      setDeleteAllConfirmation('');
      
      // Refresh archives
      await fetchArchives();
    } catch (error) {
      console.error('Error deleting all archives:', error);
      toast.error('Fehler beim Löschen aller Archive: ' + (error.response?.data?.detail || error.message));
    }
  };

  const openDeleteDialog = (archive) => {
    setArchiveToDelete(archive);
    setDeleteConfirmation('');
    setShowDeleteDialog(true);
  };

  const openDeleteAllDialog = () => {
    setDeleteAllConfirmation('');
    setShowDeleteAllDialog(true);
  };

  const viewArchiveDetails = async (archive) => {
    try {
      const response = await axios.get(`${API}/archives/${archive.id}`);
      setSelectedArchive(response.data);
      setShowArchiveDetailsDialog(true);
    } catch (error) {
      console.error('Error fetching archive details:', error);
      toast.error('Failed to fetch archive details');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('de-DE', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getMonthName = (month) => {
    const months = [
      "Januar", "Februar", "März", "April", "Mai", "Juni",
      "Juli", "August", "September", "Oktober", "November", "Dezember"
    ];
    return months[month - 1];
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2">Lade Archive...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Archive Button */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Archive className="w-6 h-6 text-blue-600" />
            Inventar-Historie
          </h2>
          <p className="text-slate-600">Archivierte Fahrzeug-Bestände der letzten 6 Monate</p>
        </div>
        
        {user.role === 'admin' && (
          <div className="flex gap-2">
            <Dialog open={showArchiveDialog} onOpenChange={setShowArchiveDialog}>
              <DialogTrigger asChild>
                <Button className="flex items-center gap-2">
                  <Archive className="w-4 h-4" />
                  Monat Archivieren
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Monatliches Archiv erstellen</DialogTitle>
                  <DialogDescription>
                    Alle aktuellen Fahrzeuge für den gewählten Monat werden archiviert.
                    Dies kann nicht rückgängig gemacht werden.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div>
                    <Label htmlFor="archive-name">Archiv-Name</Label>
                    <Input
                      id="archive-name"
                      placeholder="z.B. Februar 2024 Inventur"
                      value={archiveFormData.archive_name}
                      onChange={(e) => setArchiveFormData({
                        ...archiveFormData,
                        archive_name: e.target.value
                      })}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="archive-month">Monat</Label>
                      <Input
                        id="archive-month"
                        type="number"
                        min="1"
                        max="12"
                        value={archiveFormData.month}
                        onChange={(e) => setArchiveFormData({
                          ...archiveFormData,
                          month: parseInt(e.target.value)
                        })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="archive-year">Jahr</Label>
                      <Input
                        id="archive-year"
                        type="number"
                        min="2020"
                        max="2030"
                        value={archiveFormData.year}
                        onChange={(e) => setArchiveFormData({
                          ...archiveFormData,
                          year: parseInt(e.target.value)
                        })}
                      />
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button onClick={createMonthlyArchive} className="w-full">
                    Archiv erstellen
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            {/* Delete All Archives Button */}
            {archives.length > 0 && (
              <Button 
                variant="destructive" 
                onClick={openDeleteAllDialog}
                className="flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Alle Archive löschen
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Archives Grid */}
      {archives.length === 0 ? (
        <div className="text-center py-12">
          <Archive className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-600 mb-2">Keine Archive vorhanden</h3>
          <p className="text-gray-500">
            {user.role === 'admin' 
              ? 'Erstellen Sie Ihr erstes Archiv, indem Sie den aktuellen Monatsbestand archivieren.'
              : 'Noch keine Archive verfügbar.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {archives.map((archive) => (
            <Card key={archive.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{archive.archive_name}</CardTitle>
                    <CardDescription>
                      {getMonthName(archive.month)} {archive.year}
                    </CardDescription>
                  </div>
                  <Badge variant="outline" className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    Archiviert
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="bg-slate-50 rounded-lg p-2">
                      <div className="text-lg font-bold text-slate-800">{archive.total_cars}</div>
                      <div className="text-xs text-slate-600">Gesamt</div>
                    </div>
                    <div className="bg-green-50 rounded-lg p-2">
                      <div className="text-lg font-bold text-green-600">{archive.present_cars}</div>
                      <div className="text-xs text-green-600">Anwesend</div>
                    </div>
                    <div className="bg-red-50 rounded-lg p-2">
                      <div className="text-lg font-bold text-red-600">{archive.absent_cars}</div>
                      <div className="text-xs text-red-600">Abwesend</div>
                    </div>
                  </div>

                  {/* Archive Details */}
                  <div className="text-sm text-slate-600">
                    <p>Archiviert am: {formatDate(archive.archived_at)}</p>
                    <p>Anwesend: {((archive.present_cars / archive.total_cars) * 100).toFixed(1)}%</p>
                  </div>

                  {/* View Details Button */}
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => viewArchiveDetails(archive)}
                      className="flex-1 flex items-center gap-2"
                    >
                      <Eye className="w-4 h-4" />
                      Details anzeigen
                    </Button>
                    
                    {/* Delete Button (Admin only) */}
                    {user.role === 'admin' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openDeleteDialog(archive)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Archive Details Dialog */}
      <Dialog open={showArchiveDetailsDialog} onOpenChange={setShowArchiveDetailsDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Archive className="w-5 h-5" />
              {selectedArchive?.archive_name}
            </DialogTitle>
            <DialogDescription>
              {selectedArchive && `${getMonthName(selectedArchive.month)} ${selectedArchive.year} - ${selectedArchive.total_cars} Fahrzeuge`}
            </DialogDescription>
          </DialogHeader>
          
          {selectedArchive && (
            <div className="space-y-4">
              {/* Archive Stats */}
              <div className="grid grid-cols-4 gap-4">
                <div className="bg-slate-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-slate-800">{selectedArchive.total_cars}</div>
                  <div className="text-sm text-slate-600">Gesamt Fahrzeuge</div>
                </div>
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-green-600">{selectedArchive.present_cars}</div>
                  <div className="text-sm text-green-600">Anwesend</div>
                </div>
                <div className="bg-red-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-red-600">{selectedArchive.absent_cars}</div>
                  <div className="text-sm text-red-600">Abwesend</div>
                </div>
                <div className="bg-blue-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {((selectedArchive.present_cars / selectedArchive.total_cars) * 100).toFixed(1)}%
                  </div>
                  <div className="text-sm text-blue-600">Anwesend %</div>
                </div>
              </div>

              {/* Cars Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
                {selectedArchive.cars_data.map((car) => {
                  const displayImage = car.status === 'present' && car.car_photo 
                    ? `data:image/jpeg;base64,${car.car_photo}` 
                    : car.image_url;
                  
                  const isVerificationPhoto = car.status === 'present' && car.car_photo;
                  
                  return (
                    <Card key={car.id} className="overflow-hidden">
                      {displayImage && (
                        <div className="h-32 bg-gray-200 overflow-hidden relative">
                          <img
                            src={displayImage}
                            alt={`${car.make} ${car.model}`}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                          {isVerificationPhoto && (
                            <div className="absolute top-1 left-1 bg-green-600 text-white px-1 py-0.5 rounded text-xs flex items-center gap-1">
                              <Camera className="w-2 h-2" />
                              Verified
                            </div>
                          )}
                          {car.status === 'present' && car.vin_photo && (
                            <button
                              onClick={() => {
                                const vinImage = `data:image/jpeg;base64,${car.vin_photo}`;
                                const newWindow = window.open();
                                newWindow.document.write(`
                                  <html>
                                    <head><title>VIN Verification - ${car.make} ${car.model}</title></head>
                                    <body style="margin:0; display:flex; justify-content:center; align-items:center; min-height:100vh; background:#000;">
                                      <img src="${vinImage}" style="max-width:100%; max-height:100%; object-fit:contain;" alt="VIN Verification Photo" />
                                    </body>
                                  </html>
                                `);
                              }}
                              className="absolute top-1 right-1 bg-blue-600 text-white p-0.5 rounded hover:bg-blue-700 transition-colors"
                              title="VIN-Foto anzeigen"
                            >
                              <FileText className="w-2 h-2" />
                            </button>
                          )}
                        </div>
                      )}
                      <CardHeader className="p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <CardTitle className="text-sm">{car.make} {car.model}</CardTitle>
                            <CardDescription className="text-xs">Nr. {car.number}</CardDescription>
                          </div>
                          <Badge variant={car.status === 'present' ? 'default' : 'destructive'} className="text-xs">
                            {car.status === 'present' ? 'Anwesend' : 'Abwesend'}
                            {car.status === 'present' && car.car_photo && (
                              <Camera className="w-2 h-2 ml-1" title="Foto verifiziert" />
                            )}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="p-3 pt-0">
                        <div className="space-y-1 text-xs">
                          {car.purchase_date && (
                            <p className="text-blue-600 font-medium">
                              Eingekauft: {new Date(car.purchase_date).toLocaleDateString('de-DE')}
                            </p>
                          )}
                          {car.vin && (
                            <p className="text-gray-600">VIN: {car.vin}</p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button onClick={() => setShowArchiveDetailsDialog(false)}>
              Schließen
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default History;